from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import Answer, Player, Question, Room
from .room_cache import (
    answer_exists as cache_answer_exists,
    flush_runtime_force,
    get_answer_progress,
    get_player_nickname,
    get_runtime_for_code,
    join_player,
    maybe_flush,
    record_answer,
    update_player_avatar,
)
from .text_utils import (
    SHORT_ANSWER_MAX_LENGTH,
    normalize_word_cloud_text,
)
from .utils import calculate_points, can_accept_answer, get_my_result, get_room_state
from .word_cloud import aggregate_word_cloud

logger = logging.getLogger(__name__)

DANMAKU_MAX_LENGTH = 40
DANMAKU_COOLDOWN_SEC = 2
_danmaku_cooldown = {}


def broadcast_room(room_code, event_type, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'room_{room_code}',
        {'type': 'room_message', 'event': event_type, 'data': data},
    )


class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'room_{self.room_code}'

        try:
            self.room = await self.get_room()
        except Room.DoesNotExist:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'join':
                await self.handle_join(data)
            elif action == 'start_game':
                await self.handle_start_game()
            elif action == 'next_question':
                await self.handle_next_question()
            elif action == 'submit_answer':
                await self.handle_submit_answer(data)
            elif action == 'end_question':
                await self.handle_end_question()
            elif action == 'get_state':
                await self.send_state()
            elif action == 'send_danmaku':
                await self.handle_send_danmaku(data)
            elif action == 'update_avatar':
                await self.handle_update_avatar(data)
        except json.JSONDecodeError:
            await self._send_error('无效的消息格式')
        except Exception:
            logger.exception('WebSocket action failed room=%s', getattr(self, 'room_code', '?'))
            await self._send_error('服务器处理失败，请刷新页面后重试')

    async def _send_error(self, message: str):
        await self.send(text_data=json.dumps({
            'event': 'error',
            'data': {'message': message},
        }))

    async def room_message(self, event):
        data = event['data']
        if event['event'] in ('question_ended', 'ranking_shown') and getattr(self, 'session_id', None):
            question = (data or {}).get('question') or {}
            question_id = question.get('id')
            if question_id:
                try:
                    runtime = await database_sync_to_async(get_runtime_for_code)(self.room_code)
                    my_result = await database_sync_to_async(get_my_result)(
                        runtime, self.session_id, question_id,
                    )
                    data = dict(data or {})
                    data['my_result'] = my_result
                except Exception:
                    logger.exception(
                        'Failed to attach my_result room=%s', self.room_code,
                    )
        await self.send(text_data=json.dumps({
            'event': event['event'],
            'data': data,
        }))

    async def handle_join(self, data):
        nickname = data.get('nickname', '').strip()
        session_id = data.get('session_id', '')
        avatar = data.get('avatar')

        if not nickname or len(nickname) > 50:
            await self.send(text_data=json.dumps({
                'event': 'error',
                'data': {'message': '请输入有效昵称'},
            }))
            return

        if not session_id:
            session_id = str(uuid.uuid4())

        room = await self.get_room()
        runtime = await database_sync_to_async(get_runtime_for_code)(self.room_code)
        player, _created, error = await database_sync_to_async(join_player)(
            runtime, nickname, session_id, avatar=avatar,
        )
        if error == 'nickname_taken':
            await self.send(text_data=json.dumps({
                'event': 'error',
                'data': {'message': '该昵称已被使用'},
            }))
            return

        self.session_id = session_id
        self.player_id = player.db_id
        self.runtime = runtime

        state = await self.get_room_state_async()
        asyncio.create_task(self._flush_runtime_async(runtime))

        if runtime.should_broadcast_join():
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'room_message',
                    'event': 'player_joined',
                    'data': {
                        'player_count': state['player_count'],
                        'leaderboard': state['leaderboard'],
                    },
                },
            )

        my_result = None
        question = state.get('question') or {}
        if state.get('status') in Room.SETTLEMENT_STATUSES and question.get('id'):
            my_result = await database_sync_to_async(get_my_result)(
                runtime, session_id, question['id'],
            )

        await self.send(text_data=json.dumps({
            'event': 'joined',
            'data': {
                'session_id': session_id,
                'player_id': player.db_id,
                'nickname': player.nickname,
                'avatar': player.avatar,
                'state': state,
                'my_result': my_result,
            },
        }))

    async def handle_update_avatar(self, data):
        if not hasattr(self, 'session_id'):
            return
        avatar = data.get('avatar')
        if not isinstance(avatar, dict):
            return

        runtime = await database_sync_to_async(get_runtime_for_code)(self.room_code)
        player, ok = await database_sync_to_async(update_player_avatar)(
            runtime, self.session_id, avatar,
        )
        if not ok or not player:
            return

        state = await self.get_room_state_async()
        asyncio.create_task(self._flush_runtime_async(runtime))

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'room_message',
                'event': 'avatar_updated',
                'data': {
                    'session_id': self.session_id,
                    'nickname': player.nickname,
                    'avatar': player.avatar,
                    'leaderboard': state['leaderboard'],
                },
            },
        )

    async def handle_start_game(self):
        state, error = await database_sync_to_async(start_game_for_room)(self.room_code)
        if error:
            await self._send_error(error)
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'room_message', 'event': 'game_started', 'data': state},
        )

    async def handle_next_question(self):
        state, event, error = await database_sync_to_async(advance_question_for_room)(self.room_code)
        if error:
            await self._send_error(error)
            return
        if not state or not event:
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'room_message', 'event': event, 'data': state},
        )

    async def handle_submit_answer(self, data):
        if not hasattr(self, 'session_id'):
            return

        room = await self.get_room()
        question = await self.get_current_question()
        if not question or question.question_type == Question.TYPE_EXPLANATION:
            return
        accepting = await database_sync_to_async(can_accept_answer)(room, question)
        if not accepting:
            await self.send(text_data=json.dumps({
                'event': 'answer_rejected',
                'data': {'reason': 'countdown'},
            }))
            return

        selected = self.normalize_answer_selection(question, data)
        if selected is None:
            return

        question_id = question.pk
        question_type = question.question_type
        time_limit = question.time_limit

        runtime = await database_sync_to_async(get_runtime_for_code)(self.room_code)
        exists = await database_sync_to_async(cache_answer_exists)(
            runtime, self.session_id, question_id,
        )
        if exists:
            return

        response_time_ms = data.get('response_time_ms', 0)
        is_correct, points = await database_sync_to_async(score_answer)(
            question_id, selected, response_time_ms,
        )

        recorded = await database_sync_to_async(record_answer)(
            runtime,
            self.session_id,
            question_id,
            selected,
            is_correct,
            points,
            response_time_ms,
        )
        if not recorded:
            return

        asyncio.create_task(self._flush_runtime_async(runtime))

        await self.send(text_data=json.dumps({
            'event': 'answer_received',
            'data': {
                'no_score': question_type == Question.TYPE_WORD_CLOUD,
                'selected_option': selected,
                'answer_text': selected,
            },
        }))

        try:
            progress = await database_sync_to_async(get_answer_progress)(runtime, question_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'room_message', 'event': 'answers_updated', 'data': progress},
            )
        except Exception:
            logger.exception('Failed to broadcast answer progress room=%s', self.room_code)

        try:
            await self._after_answer_recorded(question_id, question_type, runtime)
        except Exception:
            logger.exception('Post-answer processing failed room=%s', self.room_code)

    async def _after_answer_recorded(self, question_id: int, question_type: str, runtime):
        if question_type == Question.TYPE_WORD_CLOUD:
            cloud = await database_sync_to_async(aggregate_word_cloud)(
                self.room_code, question_id, runtime,
            )
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'room_message',
                    'event': 'word_cloud_updated',
                    'data': {'words': cloud},
                },
            )

        # 全员作答后仍由老师手动结束本题，不自动揭晓。

    async def handle_end_question(self):
        try:
            state, event = await database_sync_to_async(end_question_for_room)(self.room_code)
            if state is None:
                return
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'room_message', 'event': event or 'question_ended', 'data': state},
            )
        except Exception:
            logger.exception('Failed to end question room=%s', self.room_code)

    async def handle_send_danmaku(self, data):
        if not hasattr(self, 'session_id'):
            return

        room = await self.get_room()
        if room.status == Room.STATUS_ENDED:
            return

        text = data.get('text', '').strip()
        if not text:
            return
        text = text[:DANMAKU_MAX_LENGTH]

        now = time.monotonic()
        last = _danmaku_cooldown.get(self.session_id, 0)
        if now - last < DANMAKU_COOLDOWN_SEC:
            await self.send(text_data=json.dumps({
                'event': 'danmaku_rejected',
                'data': {'message': f'发送太频繁，请 {DANMAKU_COOLDOWN_SEC} 秒后再试'},
            }))
            return
        _danmaku_cooldown[self.session_id] = now

        runtime = await database_sync_to_async(get_runtime_for_code)(self.room_code)
        nickname = await database_sync_to_async(get_player_nickname)(runtime, self.session_id)
        if not nickname and self.player_id:
            player = await Player.objects.aget(id=self.player_id)
            nickname = player.nickname
        if not nickname:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'room_message',
                'event': 'danmaku',
                'data': {'nickname': nickname, 'text': text},
            },
        )

    async def send_state(self):
        state = await self.get_room_state_async()
        if (
            getattr(self, 'session_id', None)
            and state.get('status') in Room.SETTLEMENT_STATUSES
        ):
            question = state.get('question') or {}
            question_id = question.get('id')
            if question_id:
                try:
                    runtime = await database_sync_to_async(get_runtime_for_code)(self.room_code)
                    state = dict(state)
                    state['my_result'] = await database_sync_to_async(get_my_result)(
                        runtime, self.session_id, question_id,
                    )
                except Exception:
                    logger.exception(
                        'Failed to attach my_result on get_state room=%s', self.room_code,
                    )
        await self.send(text_data=json.dumps({'event': 'state', 'data': state}))

    async def _flush_runtime_async(self, runtime, force=False):
        if force:
            await database_sync_to_async(flush_runtime_force)(runtime)
        else:
            await database_sync_to_async(maybe_flush)(runtime)

    async def get_room(self):
        return await Room.objects.aget(code=self.room_code)

    async def get_questions_count(self):
        room = await self.get_room()
        return await room.room_questions.acount()

    async def get_current_question(self):
        room = await self.get_room()
        questions = [rq.question async for rq in room.room_questions.select_related('question').order_by('order').all()]
        if 0 <= room.current_question_index < len(questions):
            return questions[room.current_question_index]
        return None

    async def update_room(self, **kwargs):
        room = await self.get_room()
        for key, value in kwargs.items():
            setattr(room, key, value)
        await room.asave(update_fields=list(kwargs.keys()))

    async def get_room_state_async(self):
        return await database_sync_to_async(get_room_state_by_code)(self.room_code)

    @staticmethod
    def normalize_answer_selection(question, data):
        if question.question_type in (Question.TYPE_SHORT_ANSWER, Question.TYPE_WORD_CLOUD):
            text = data.get('answer_text', '').strip()
            if not text:
                return None
            if question.question_type == Question.TYPE_WORD_CLOUD:
                return normalize_word_cloud_text(text)
            return text[:SHORT_ANSWER_MAX_LENGTH]

        if question.question_type == Question.TYPE_MULTIPLE:
            options = data.get('selected_options', [])
            if not isinstance(options, list) or not options:
                return None
            valid = sorted({
                opt.upper() for opt in options
                if isinstance(opt, str) and opt.upper() in ('A', 'B', 'C', 'D')
            })
            if not valid:
                return None
            return ','.join(valid)

        selected = data.get('selected_option', '').upper()
        if selected not in ('A', 'B', 'C', 'D'):
            return None
        return selected


def score_answer(question_id: int, selected: str, response_time_ms: int) -> tuple[bool, int]:
    question = Question.objects.get(pk=question_id)
    if question.question_type in Question.UNSCORED_TYPES:
        return False, 0
    if question.question_type == Question.TYPE_SHORT_ANSWER:
        is_correct = question.is_text_answer_correct(selected)
    elif question.question_type == Question.TYPE_MULTIPLE:
        is_correct = question.is_multiple_choice_correct(selected)
    else:
        is_correct = question.is_answer_correct(selected)
    points = calculate_points(question.time_limit, response_time_ms, is_correct)
    return is_correct, points


def _advance_to_next_question(room, runtime) -> tuple[dict | None, str | None, str | None]:
    questions_count = room.room_questions.count()
    if room.current_question_index + 1 >= questions_count:
        room.status = Room.STATUS_ENDED
        room.save(update_fields=['status'])
        return get_room_state(room, runtime=runtime), 'game_ended', None

    room.status = Room.STATUS_PLAYING
    room.current_question_index += 1
    room.question_started_at = timezone.now()
    room.save(update_fields=['status', 'current_question_index', 'question_started_at'])
    return get_room_state(room, runtime=runtime), 'question_started', None


def _flush_runtime(room_code: str, runtime):
    try:
        flush_runtime_force(runtime)
    except Exception:
        logger.exception('Flush failed room=%s', room_code)


def end_question_for_room(room_code: str) -> tuple[dict | None, str | None]:
    room = Room.objects.get(code=room_code)
    if room.status != Room.STATUS_PLAYING:
        return None, None
    runtime = get_runtime_for_code(room_code)
    _flush_runtime(room_code, runtime)
    current = room.current_question()
    if current and current.question_type == Question.TYPE_EXPLANATION:
        state, event, _error = _advance_to_next_question(room, runtime)
        return state, event
    room.status = Room.STATUS_REVEAL
    room.save(update_fields=['status'])
    return get_room_state(room, runtime=runtime), 'question_ended'


def advance_question_for_room(room_code: str) -> tuple[dict | None, str | None, str | None]:
    room = Room.objects.get(code=room_code)
    runtime = get_runtime_for_code(room_code)
    _flush_runtime(room_code, runtime)

    if room.status == Room.STATUS_PLAYING:
        current = room.current_question()
        if current and current.question_type == Question.TYPE_EXPLANATION:
            return _advance_to_next_question(room, runtime)
        return None, None, '当前不是题目结算阶段，请稍候再试'

    if room.status == Room.STATUS_REVEAL:
        room.status = Room.STATUS_LEADERBOARD
        room.save(update_fields=['status'])
        return get_room_state(room, runtime=runtime), 'ranking_shown', None

    if room.status != Room.STATUS_LEADERBOARD:
        return None, None, '当前不是题目结算阶段，请稍候再试'

    return _advance_to_next_question(room, runtime)


def start_game_for_room(room_code: str) -> tuple[dict | None, str | None]:
    """Start game: update DB and broadcast state; flush players in background-safe order."""
    room = Room.objects.get(code=room_code)
    if room.status != Room.STATUS_WAITING:
        return None, '游戏已开始或已结束'
    if room.room_questions.count() == 0:
        return None, '房间内没有题目，无法开始游戏'

    room.status = Room.STATUS_PLAYING
    room.current_question_index = 0
    room.question_started_at = timezone.now()
    room.save(update_fields=['status', 'current_question_index', 'question_started_at'])

    runtime = get_runtime_for_code(room_code)
    try:
        flush_runtime_force(runtime)
    except Exception:
        logger.exception('Player flush failed when starting room %s', room_code)

    return get_room_state(room, runtime=runtime), None


def get_room_state_by_code(room_code):
    room = Room.objects.get(code=room_code)
    runtime = get_runtime_for_code(room_code)
    return get_room_state(room, runtime=runtime)
