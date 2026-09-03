"""In-memory room cache with batched DB writes (space-for-time under load)."""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field

from django.conf import settings
from django.db import IntegrityError, transaction

from .models import Answer, Player, Room

FLUSH_BATCH = getattr(settings, 'ROOM_CACHE_FLUSH_BATCH', 30)
FLUSH_INTERVAL = getattr(settings, 'ROOM_CACHE_FLUSH_INTERVAL', 0.5)
JOIN_BROADCAST_INTERVAL = getattr(settings, 'ROOM_CACHE_JOIN_BROADCAST_INTERVAL', 0.25)


@dataclass
class CachedPlayer:
    session_id: str
    nickname: str
    score: int = 0
    db_id: int | None = None
    joined_at: float = field(default_factory=time.time)
    score_dirty: bool = False
    avatar: dict = field(default_factory=lambda: {'face': 0, 'hair': 0})
    avatar_dirty: bool = False


@dataclass
class PendingAnswer:
    session_id: str
    question_id: int
    selected: str
    is_correct: bool
    points: int
    response_time_ms: int


class RoomRuntime:
    def __init__(self, room_id: int, room_code: str):
        self.room_id = room_id
        self.room_code = room_code
        self.lock = threading.Lock()
        self.players: dict[str, CachedPlayer] = {}
        self.nicknames: dict[str, str] = {}
        self.answers: set[tuple[str, int]] = set()
        self.answer_records: dict[tuple[str, int], PendingAnswer] = {}
        self.answer_counts: dict[int, int] = {}
        self.pending_players: list[CachedPlayer] = []
        self.pending_answers: list[PendingAnswer] = []
        self.hydrated = False
        self.last_flush_at = 0.0
        self.last_join_broadcast_at = 0.0

    def player_count(self) -> int:
        return len(self.players)

    def get_leaderboard(self) -> list[dict]:
        ordered = sorted(
            self.players.values(),
            key=lambda p: (-p.score, p.joined_at),
        )
        return [
            {
                'nickname': p.nickname,
                'score': p.score,
                'rank': i + 1,
                'avatar': p.avatar,
            }
            for i, p in enumerate(ordered)
        ]

    def should_flush(self) -> bool:
        if len(self.pending_players) >= FLUSH_BATCH:
            return True
        if len(self.pending_answers) >= FLUSH_BATCH:
            return True
        pending = len(self.pending_players) + len(self.pending_answers)
        if pending and time.monotonic() - self.last_flush_at >= FLUSH_INTERVAL:
            return True
        return False

    def should_broadcast_join(self) -> bool:
        with self.lock:
            now = time.monotonic()
            if now - self.last_join_broadcast_at >= JOIN_BROADCAST_INTERVAL:
                self.last_join_broadcast_at = now
                return True
            return False


_runtimes: dict[str, RoomRuntime] = {}
_registry_lock = threading.Lock()


def get_runtime(room: Room) -> RoomRuntime:
    with _registry_lock:
        runtime = _runtimes.get(room.code)
        if runtime is None:
            runtime = RoomRuntime(room.id, room.code)
            _runtimes[room.code] = runtime
        return runtime


def get_runtime_for_code(room_code: str) -> RoomRuntime:
    room = Room.objects.get(code=room_code)
    return get_runtime(room)


def drop_runtime(room_code: str) -> None:
    with _registry_lock:
        _runtimes.pop(room_code, None)


def _clean_avatar(avatar) -> dict:
    if isinstance(avatar, dict):
        try:
            return {
                'face': max(0, int(avatar.get('face', 0))),
                'hair': max(0, int(avatar.get('hair', 0))),
            }
        except (ValueError, TypeError):
            pass
    return {'face': 0, 'hair': 0}


def _hydrate_from_db(runtime: RoomRuntime) -> None:
    if runtime.hydrated:
        return
    for player in Player.objects.filter(room_id=runtime.room_id):
        cached = CachedPlayer(
            session_id=player.session_id,
            nickname=player.nickname,
            score=player.score,
            db_id=player.id,
            joined_at=player.joined_at.timestamp() if player.joined_at else time.time(),
            avatar=player.get_avatar_dict(),
        )
        runtime.players[player.session_id] = cached
        runtime.nicknames[player.nickname] = player.session_id

    player_ids = {p.db_id: p.session_id for p in runtime.players.values() if p.db_id}
    for answer in Answer.objects.filter(room_id=runtime.room_id):
        session_id = player_ids.get(answer.player_id)
        if not session_id:
            continue
        key = (session_id, answer.question_id)
        runtime.answers.add(key)
        runtime.answer_records[key] = PendingAnswer(
            session_id=session_id,
            question_id=answer.question_id,
            selected=answer.selected_option,
            is_correct=answer.is_correct,
            points=answer.points,
            response_time_ms=answer.response_time_ms,
        )
        runtime.answer_counts[answer.question_id] = (
            runtime.answer_counts.get(answer.question_id, 0) + 1
        )
    runtime.hydrated = True


def join_player(
    runtime: RoomRuntime,
    nickname: str,
    session_id: str,
    avatar: dict | None = None,
) -> tuple[CachedPlayer | None, bool, str | None]:
    with runtime.lock:
        _hydrate_from_db(runtime)
        clean_av = _clean_avatar(avatar)
        if nickname in runtime.nicknames:
            existing_sid = runtime.nicknames[nickname]
            existing = runtime.players[existing_sid]
            if existing.session_id != session_id:
                return None, False, 'nickname_taken'
            if avatar:
                existing.avatar = clean_av
                existing.avatar_dirty = True
            return existing, False, None

        player = CachedPlayer(
            session_id=session_id,
            nickname=nickname,
            avatar=clean_av,
        )
        runtime.players[session_id] = player
        runtime.nicknames[nickname] = session_id
        runtime.pending_players.append(player)
        return player, True, None


def update_player_avatar(
    runtime: RoomRuntime,
    session_id: str,
    avatar: dict,
) -> tuple[CachedPlayer | None, bool]:
    with runtime.lock:
        _hydrate_from_db(runtime)
        player = runtime.players.get(session_id)
        if not player:
            return None, False
        player.avatar = _clean_avatar(avatar)
        player.avatar_dirty = True
        return player, True


def record_answer(
    runtime: RoomRuntime,
    session_id: str,
    question_id: int,
    selected: str,
    is_correct: bool,
    points: int,
    response_time_ms: int,
) -> bool:
    with runtime.lock:
        _hydrate_from_db(runtime)
        key = (session_id, question_id)
        if key in runtime.answers:
            return False
        player = runtime.players.get(session_id)
        if not player:
            return False

        runtime.answers.add(key)
        runtime.answer_counts[question_id] = runtime.answer_counts.get(question_id, 0) + 1
        if is_correct:
            player.score += points
            player.score_dirty = True
        pending = PendingAnswer(
            session_id=session_id,
            question_id=question_id,
            selected=selected,
            is_correct=is_correct,
            points=points,
            response_time_ms=response_time_ms,
        )
        runtime.answer_records[key] = pending
        runtime.pending_answers.append(pending)
        return True


def answer_exists(runtime: RoomRuntime, session_id: str, question_id: int) -> bool:
    with runtime.lock:
        _hydrate_from_db(runtime)
        return (session_id, question_id) in runtime.answers


def get_answer_count(runtime: RoomRuntime, question_id: int) -> int:
    with runtime.lock:
        _hydrate_from_db(runtime)
        return runtime.answer_counts.get(question_id, 0)


def get_player_nickname(runtime: RoomRuntime, session_id: str) -> str | None:
    with runtime.lock:
        player = runtime.players.get(session_id)
        return player.nickname if player else None


def overlay_room_state(state: dict, runtime: RoomRuntime) -> dict:
    with runtime.lock:
        if not runtime.players:
            return state
        state = dict(state)
        state['player_count'] = runtime.player_count()
        state['leaderboard'] = runtime.get_leaderboard()
        return state


def _ensure_player_row(runtime: RoomRuntime, cached: CachedPlayer) -> int | None:
    """Idempotently persist a cached player and bind db_id.

    A previous successful insert can leave db_id empty (or a later flush can
    retry the same nickname). Unique(room, nickname) must not abort answers.
    """
    if cached.db_id:
        return cached.db_id

    existing = Player.objects.filter(
        room_id=runtime.room_id,
        nickname=cached.nickname,
    ).first()
    if existing is None:
        existing = Player.objects.filter(
            room_id=runtime.room_id,
            session_id=cached.session_id,
        ).first()

    if existing is not None:
        cached.db_id = existing.id
        updates = {}
        if existing.session_id != cached.session_id:
            updates['session_id'] = cached.session_id
        if existing.score != cached.score:
            updates['score'] = cached.score
        if updates:
            Player.objects.filter(id=existing.id).update(**updates)
        return cached.db_id

    try:
        with transaction.atomic():
            row = Player.objects.create(
                room_id=runtime.room_id,
                nickname=cached.nickname,
                session_id=cached.session_id,
                score=cached.score,
                avatar=json.dumps(cached.avatar),
            )
        cached.db_id = row.id
        return cached.db_id
    except IntegrityError:
        existing = Player.objects.filter(
            room_id=runtime.room_id,
            nickname=cached.nickname,
        ).first()
        if existing is None:
            return None
        cached.db_id = existing.id
        return cached.db_id


@transaction.atomic
def _flush_locked(runtime: RoomRuntime) -> None:
    for cached in list(runtime.players.values()):
        if cached.db_id is None:
            _ensure_player_row(runtime, cached)
    runtime.pending_players = [p for p in runtime.pending_players if p.db_id is None]

    if runtime.pending_answers:
        remaining: list[PendingAnswer] = []
        to_create: list[Answer] = []
        for pending in runtime.pending_answers:
            player = runtime.players.get(pending.session_id)
            if player and not player.db_id:
                _ensure_player_row(runtime, player)
            if not player or not player.db_id:
                remaining.append(pending)
                continue
            to_create.append(Answer(
                player_id=player.db_id,
                room_id=runtime.room_id,
                question_id=pending.question_id,
                selected_option=pending.selected,
                is_correct=pending.is_correct,
                points=pending.points,
                response_time_ms=pending.response_time_ms,
            ))
        if to_create:
            Answer.objects.bulk_create(to_create, ignore_conflicts=True)
        runtime.pending_answers = remaining

    dirty_ids = {
        p.db_id: p.score
        for p in runtime.players.values()
        if p.db_id and p.score_dirty
    }
    for db_id, score in dirty_ids.items():
        Player.objects.filter(id=db_id).update(score=score)
    for p in runtime.players.values():
        if p.db_id and p.score_dirty:
            p.score_dirty = False

    dirty_avatars = {
        p.db_id: json.dumps(p.avatar)
        for p in runtime.players.values()
        if p.db_id and p.avatar_dirty
    }
    for db_id, av_json in dirty_avatars.items():
        Player.objects.filter(id=db_id).update(avatar=av_json)
    for p in runtime.players.values():
        if p.db_id and p.avatar_dirty:
            p.avatar_dirty = False

    runtime.last_flush_at = time.monotonic()


def flush_runtime(runtime: RoomRuntime, force: bool = False) -> None:
    with runtime.lock:
        pending = len(runtime.pending_players) + len(runtime.pending_answers)
        dirty = any(p.score_dirty or p.avatar_dirty for p in runtime.players.values())
        if not force and not pending and not dirty:
            return
        if not force and not runtime.should_flush() and not dirty:
            return
        _flush_locked(runtime)


def maybe_flush(runtime: RoomRuntime) -> None:
    flush_runtime(runtime, force=False)


def flush_runtime_force(runtime: RoomRuntime) -> None:
    flush_runtime(runtime, force=True)


def get_question_answer_records(runtime: RoomRuntime, question_id: int) -> list[PendingAnswer]:
    with runtime.lock:
        _hydrate_from_db(runtime)
        return [
            rec for (sid, qid), rec in runtime.answer_records.items()
            if qid == question_id
        ]


def get_player_answer_record(
    runtime: RoomRuntime,
    session_id: str,
    question_id: int,
) -> PendingAnswer | None:
    with runtime.lock:
        _hydrate_from_db(runtime)
        return runtime.answer_records.get((session_id, question_id))


def get_runtime_pending_answers(runtime: RoomRuntime) -> list[PendingAnswer]:
    with runtime.lock:
        return list(runtime.pending_answers)


def get_runtime_players(runtime: RoomRuntime) -> list[CachedPlayer]:
    with runtime.lock:
        return list(runtime.players.values())
