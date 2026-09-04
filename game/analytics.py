"""Game room analytics calculation for post-game question and player performance."""

from __future__ import annotations

import json
import logging
from typing import Any

from .models import Answer, Player, Question, Room
from .room_cache import (
    flush_runtime_force,
    get_runtime,
    get_runtime_pending_answers,
    get_runtime_players,
)

logger = logging.getLogger(__name__)


def _format_option_answer(question: Question, selected: str) -> str:
    """Format user selection into human-readable option text."""
    if not selected:
        return '—'
    if question.question_type == Question.TYPE_SHORT_ANSWER:
        return selected
    if question.question_type == Question.TYPE_WORD_CLOUD:
        return selected
    if question.question_type == Question.TYPE_JUDGMENT:
        key = selected.strip().upper()
        if key == 'A':
            return f"A ({question.option_a or '正确'})"
        if key == 'B':
            return f"B ({question.option_b or '错误'})"
        return selected

    # Single or Multiple choice
    opt_map = {
        'A': question.option_a,
        'B': question.option_b,
        'C': question.option_c,
        'D': question.option_d,
    }
    keys = [k.strip().upper() for k in selected.split(',') if k.strip().upper() in opt_map]
    if not keys:
        return selected
    parts = [f"{k}: {opt_map.get(k, '')}" for k in keys if opt_map.get(k)]
    return ', '.join(parts) if parts else selected


def _safe_response_time_sec(response_time_ms) -> float:
    """Convert ms to seconds; tolerate None / bad values from partial flushes."""
    try:
        if response_time_ms is None:
            return 0.0
        return round(float(response_time_ms) / 1000.0, 1)
    except (TypeError, ValueError):
        return 0.0


def _safe_image_url(question: Question) -> str:
    try:
        if question.image:
            return question.image.url
    except Exception:
        logger.exception('Failed to resolve image URL for question %s', getattr(question, 'pk', None))
    return ''


def get_room_analytics_data(room: Room) -> dict[str, Any]:
    """Calculate thorough post-game analytics by question and by player."""
    try:
        runtime = get_runtime(room)
        flush_runtime_force(runtime)
    except Exception:
        logger.exception('Failed to flush runtime before analytics for room %s', room.code)

    questions = list(room.get_questions())
    players = list(Player.objects.filter(room=room).order_by('-score', 'joined_at'))
    answers = list(Answer.objects.filter(room=room).select_related('player', 'question'))

    # Overlay in-memory cache so a failed/partial flush still shows live results.
    try:
        runtime = get_runtime(room)
        cached_players = get_runtime_players(runtime)
        pending_answers = get_runtime_pending_answers(runtime)
        db_by_nick = {p.nickname: p for p in players}
        for cached in cached_players:
            existing = db_by_nick.get(cached.nickname)
            if existing is None:
                # Player answered in-memory but is not in DB yet.
                ghost = Player(
                    nickname=cached.nickname,
                    score=cached.score,
                    session_id=cached.session_id,
                    avatar=json.dumps(cached.avatar) if isinstance(cached.avatar, dict) else cached.avatar,
                )
                ghost.id = cached.db_id or (-abs(hash(cached.session_id)) or -1)
                ghost._avatar_dict = cached.avatar
                players.append(ghost)
                db_by_nick[cached.nickname] = ghost
            else:
                if cached.score > existing.score:
                    existing.score = cached.score
        players.sort(key=lambda p: (-p.score, p.pk or 0))

        nick_to_player = {p.nickname: p for p in players}
        sid_to_player = {}
        for cached in cached_players:
            mapped = nick_to_player.get(cached.nickname)
            if mapped is not None:
                sid_to_player[cached.session_id] = mapped

        class _MemAnswer:
            def __init__(self, player_id, question_id, selected, is_correct, points, response_time_ms):
                self.player_id = player_id
                self.question_id = question_id
                self.selected_option = selected
                self.is_correct = is_correct
                self.points = points
                self.response_time_ms = response_time_ms

        extra_answers = []
        for pending in pending_answers:
            mapped = sid_to_player.get(pending.session_id)
            if mapped is None or not mapped.id:
                continue
            extra_answers.append(_MemAnswer(
                mapped.id,
                pending.question_id,
                pending.selected,
                pending.is_correct,
                pending.points,
                pending.response_time_ms,
            ))
        answers = list(answers) + extra_answers
    except Exception:
        logger.exception('Failed to overlay runtime cache for analytics room %s', room.code)

    player_count = len(players)
    question_count = len(questions)

    # Keyed by (player_id, question_id)
    answer_map: dict[tuple[int, int], object] = {
        (a.player_id, a.question_id): a for a in answers
    }

    type_labels = {
        Question.TYPE_SINGLE: '单选题',
        Question.TYPE_MULTIPLE: '多选题',
        Question.TYPE_JUDGMENT: '判断题',
        Question.TYPE_SHORT_ANSWER: '简答题',
        Question.TYPE_WORD_CLOUD: '词云题',
        Question.TYPE_EXPLANATION: '解释',
    }

    # 1. By Question Analysis
    questions_analysis = []
    total_correct_answers = 0
    total_scored_questions = 0

    for idx, q in enumerate(questions, start=1):
        is_word_cloud = (q.question_type == Question.TYPE_WORD_CLOUD)
        is_explanation = (q.question_type == Question.TYPE_EXPLANATION)
        is_unscored = q.question_type in Question.UNSCORED_TYPES
        if not is_unscored:
            total_scored_questions += 1

        correct_players = []
        wrong_players = []
        unanswered_players = []

        if is_explanation:
            questions_analysis.append({
                'id': q.id,
                'order': idx,
                'text': q.text or '解释',
                'question_type': q.question_type,
                'type_label': type_labels.get(q.question_type, '选择题'),
                'correct_answer_display': q.get_correct_option_display(),
                'image_url': _safe_image_url(q),
                'accuracy_percent': None,
                'correct_count': 0,
                'wrong_count': 0,
                'unanswered_count': 0,
                'is_word_cloud': False,
                'is_explanation': True,
                'is_unscored': True,
                'correct_players': [],
                'wrong_players': [],
                'unanswered_players': [],
            })
            continue

        for p in players:
            ans = answer_map.get((p.id, q.id))
            p_avatar = p.get_avatar_dict()
            if ans is None:
                unanswered_players.append({
                    'id': p.id,
                    'nickname': p.nickname,
                    'avatar': p_avatar,
                    'rank': None,
                })
            else:
                formatted_sel = _format_option_answer(q, ans.selected_option)
                item = {
                    'id': p.id,
                    'nickname': p.nickname,
                    'avatar': p_avatar,
                    'selected': ans.selected_option,
                    'selected_display': formatted_sel,
                    'points': ans.points or 0,
                    'response_time_ms': ans.response_time_ms or 0,
                    'response_time_sec': _safe_response_time_sec(ans.response_time_ms),
                }
                if is_word_cloud or ans.is_correct:
                    correct_players.append(item)
                    if not is_word_cloud:
                        total_correct_answers += 1
                else:
                    wrong_players.append(item)

        total_ans_count = len(correct_players) + len(wrong_players)
        accuracy_percent = (
            round((len(correct_players) / player_count) * 100, 1)
            if player_count > 0 and not is_word_cloud
            else (100.0 if is_word_cloud and total_ans_count > 0 else 0.0)
        )

        questions_analysis.append({
            'id': q.id,
            'order': idx,
            'text': q.text,
            'question_type': q.question_type,
            'type_label': type_labels.get(q.question_type, '选择题'),
            'correct_answer_display': q.get_correct_option_display(),
            'image_url': _safe_image_url(q),
            'accuracy_percent': accuracy_percent,
            'correct_count': len(correct_players),
            'wrong_count': len(wrong_players),
            'unanswered_count': len(unanswered_players),
            'is_word_cloud': is_word_cloud,
            'is_explanation': False,
            'is_unscored': is_unscored,
            'correct_players': correct_players,
            'wrong_players': wrong_players,
            'unanswered_players': unanswered_players,
        })

    # 2. By Player Analysis
    players_analysis = []
    for rank_idx, p in enumerate(players, start=1):
        p_avatar = p.get_avatar_dict()
        correct_list = []
        wrong_list = []
        unanswered_list = []

        for idx, q in enumerate(questions, start=1):
            if q.question_type == Question.TYPE_EXPLANATION:
                continue
            ans = answer_map.get((p.id, q.id))
            is_word_cloud = (q.question_type == Question.TYPE_WORD_CLOUD)
            correct_display = q.get_correct_option_display()

            if ans is None:
                unanswered_list.append({
                    'order': idx,
                    'question_id': q.id,
                    'text': q.text,
                    'question_type': q.question_type,
                    'type_label': type_labels.get(q.question_type, '选择题'),
                    'correct_answer_display': correct_display,
                })
            else:
                formatted_sel = _format_option_answer(q, ans.selected_option)
                q_item = {
                    'order': idx,
                    'question_id': q.id,
                    'text': q.text,
                    'question_type': q.question_type,
                    'type_label': type_labels.get(q.question_type, '选择题'),
                    'selected': ans.selected_option,
                    'selected_display': formatted_sel,
                    'correct_answer_display': correct_display,
                    'points': ans.points or 0,
                    'response_time_sec': _safe_response_time_sec(ans.response_time_ms),
                    'is_word_cloud': is_word_cloud,
                }
                if is_word_cloud or ans.is_correct:
                    correct_list.append(q_item)
                else:
                    wrong_list.append(q_item)

        # Explanation-only / unscored-only rooms have 0 scored questions — do not fake a divisor.
        if total_scored_questions > 0:
            p_accuracy = round((len(correct_list) / total_scored_questions) * 100, 1)
        else:
            p_accuracy = None

        players_analysis.append({
            'id': p.id,
            'nickname': p.nickname,
            'avatar': p_avatar,
            'score': p.score or 0,
            'rank': rank_idx,
            'accuracy_percent': p_accuracy,
            'correct_count': len(correct_list),
            'wrong_count': len(wrong_list),
            'unanswered_count': len(unanswered_list),
            'correct_questions': correct_list,
            'wrong_questions': wrong_list,
            'unanswered_questions': unanswered_list,
            'has_scored_questions': total_scored_questions > 0,
        })

    # 3. Overall Summary
    total_possible_correct = player_count * total_scored_questions
    overall_accuracy = (
        round((total_correct_answers / total_possible_correct) * 100, 1)
        if total_possible_correct > 0
        else None
    )
    avg_score = (
        round(sum((p.score or 0) for p in players) / player_count, 1)
        if player_count > 0
        else 0.0
    )
    highest_score = max(((p.score or 0) for p in players), default=0)

    # Most difficult / easiest questions (skip unscored: explanation / word cloud)
    scored_questions = [
        qa for qa in questions_analysis
        if not qa.get('is_unscored') and qa.get('accuracy_percent') is not None
    ]
    hardest_q = min(scored_questions, key=lambda x: x['accuracy_percent']) if scored_questions else None
    easiest_q = max(scored_questions, key=lambda x: x['accuracy_percent']) if scored_questions else None

    return {
        'room': {
            'id': room.id,
            'code': room.code,
            'name': room.name,
            'status': room.status,
            'created_at': room.created_at.strftime('%Y-%m-%d %H:%M') if room.created_at else '',
        },
        'summary': {
            'total_players': player_count,
            'total_questions': question_count,
            'total_scored_questions': total_scored_questions,
            'has_scored_questions': total_scored_questions > 0,
            'overall_accuracy': overall_accuracy,
            'avg_score': avg_score,
            'highest_score': highest_score,
            'hardest_question': {
                'order': hardest_q['order'],
                'text': hardest_q['text'],
                'accuracy': hardest_q['accuracy_percent'],
            } if hardest_q else None,
            'easiest_question': {
                'order': easiest_q['order'],
                'text': easiest_q['text'],
                'accuracy': easiest_q['accuracy_percent'],
            } if easiest_q else None,
        },
        'by_questions': questions_analysis,
        'by_players': players_analysis,
    }
