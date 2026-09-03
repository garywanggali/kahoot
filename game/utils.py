from django.utils import timezone

from .models import Answer, Player, Question, Room
from .question_save import _question_image_url
from .validators import MAX_QUESTION_IMAGE_BYTES

QUESTION_COUNTDOWN_SECONDS = 3


def question_uses_countdown(question) -> bool:
    if not question:
        return True
    if getattr(question, 'question_type', None) == Question.TYPE_EXPLANATION:
        return False
    if int(getattr(question, 'time_limit', 0) or 0) <= 0:
        return False
    return True


def question_countdown_remaining_ms(room, now=None, question=None) -> int:
    """Milliseconds left in the 3-2-1 intro before answering starts.

    Do not query related questions here: this runs from the async websocket
    consumer on every submit, so extra ORM would crash the handler.
    """
    if getattr(room, 'status', None) != Room.STATUS_PLAYING:
        return 0
    if question is not None and not question_uses_countdown(question):
        return 0
    started = getattr(room, 'question_started_at', None)
    if not started:
        return 0
    now = now or timezone.now()
    elapsed_ms = int((now - started).total_seconds() * 1000)
    return max(0, QUESTION_COUNTDOWN_SECONDS * 1000 - elapsed_ms)


def can_accept_answer(room, question=None) -> bool:
    return (
        getattr(room, 'status', None) == Room.STATUS_PLAYING
        and question_countdown_remaining_ms(room, question=question) <= 0
    )


def build_question_reveal(room, question, runtime=None) -> dict:
    """Public reveal payload after a question ends: option bars + correct answer."""
    player_count = room.players.count()
    records = []
    if runtime is not None:
        from .room_cache import get_question_answer_records, overlay_room_state
        records = get_question_answer_records(runtime, question.id)
        overlay = overlay_room_state({'player_count': player_count}, runtime)
        player_count = overlay.get('player_count', player_count)
    else:
        records = [
            type('Rec', (), {
                'selected': a.selected_option,
                'is_correct': a.is_correct,
            })()
            for a in Answer.objects.filter(room=room, question=question)
        ]

    answered_count = len(records)
    correct_count = sum(1 for r in records if r.is_correct)
    unanswered_count = max(0, player_count - answered_count)

    option_stats = []
    if question.question_type in (
        Question.TYPE_SINGLE,
        Question.TYPE_MULTIPLE,
        Question.TYPE_JUDGMENT,
    ):
        correct_keys = question.get_correct_option_set()
        counts = {opt['key']: 0 for opt in question.get_options()}
        for rec in records:
            for part in str(rec.selected or '').upper().split(','):
                key = part.strip()
                if key in counts:
                    counts[key] += 1
        option_stats = [
            {
                'key': opt['key'],
                'text': opt['text'],
                'count': counts.get(opt['key'], 0),
                'is_correct': opt['key'] in correct_keys,
            }
            for opt in question.get_options()
        ]

    return {
        'option_stats': option_stats,
        'answered_count': answered_count,
        'correct_count': correct_count,
        'wrong_count': max(0, answered_count - correct_count),
        'unanswered_count': unanswered_count,
        'player_count': player_count,
        'correct_answer_display': question.get_correct_option_display(),
    }


def get_my_result(runtime, session_id: str, question_id: int) -> dict:
    from .room_cache import get_player_answer_record
    rec = get_player_answer_record(runtime, session_id, question_id) if runtime else None
    question = Question.objects.filter(pk=question_id).only('question_type').first()
    no_score = bool(question and question.question_type in Question.UNSCORED_TYPES)
    if rec is None:
        return {'answered': False, 'is_correct': False, 'points': 0, 'no_score': no_score}
    return {
        'answered': True,
        'is_correct': bool(rec.is_correct),
        'points': rec.points,
        'no_score': no_score,
    }


def calculate_points(time_limit_seconds, response_time_ms, is_correct):
    if not is_correct:
        return 0
    time_limit_ms = time_limit_seconds * 1000
    if response_time_ms >= time_limit_ms:
        return 0
    ratio = 1 - (response_time_ms / time_limit_ms)
    return max(0, int(1000 * ratio))


def get_leaderboard(room):
    players = Player.objects.filter(room=room).order_by('-score', 'joined_at')
    return [
        {
            'nickname': p.nickname,
            'score': p.score,
            'rank': i + 1,
            'avatar': p.get_avatar_dict(),
        }
        for i, p in enumerate(players)
    ]


def get_room_state(room, runtime=None):
    questions = room.get_questions()
    current_q = room.current_question()
    state = {
        'code': room.code,
        'name': room.name,
        'status': room.status,
        'current_question_index': room.current_question_index,
        'total_questions': len(questions),
        'player_count': room.players.count(),
        'leaderboard': get_leaderboard(room),
        'show_question_stem': bool(getattr(room, 'show_question_stem', True)),
        'countdown_seconds': QUESTION_COUNTDOWN_SECONDS,
        'countdown_remaining_ms': question_countdown_remaining_ms(room, question=current_q),
        'answered_count': 0,
    }
    if current_q and room.status in (Room.STATUS_PLAYING, *Room.SETTLEMENT_STATUSES):
        question_data = {
            'id': current_q.id,
            'text': current_q.text,
            'question_type': current_q.question_type,
            'options': current_q.get_options(),
            'time_limit': current_q.time_limit,
            'no_score': current_q.question_type in Question.UNSCORED_TYPES,
        }
        if room.status in Room.SETTLEMENT_STATUSES:
            if current_q.question_type == Question.TYPE_MULTIPLE:
                question_data['correct_options'] = sorted(current_q.get_correct_option_set())
            elif current_q.question_type == Question.TYPE_JUDGMENT:
                key = current_q.correct_option.strip().upper()
                question_data['correct_option'] = (
                    current_q.option_a if key == 'A' else current_q.option_b
                )
            elif current_q.question_type == Question.TYPE_SHORT_ANSWER:
                question_data['correct_answer'] = current_q.option_a.replace('|', ' / ')
            elif current_q.question_type not in Question.UNSCORED_TYPES:
                question_data['correct_option'] = current_q.correct_option
            question_data['reveal'] = build_question_reveal(room, current_q, runtime)
        if current_q.image:
            question_data['image_url'] = _question_image_url(current_q)
        state['question'] = question_data
    if runtime is not None:
        from .room_cache import overlay_room_state
        state = overlay_room_state(state, runtime)
    from .word_cloud import attach_word_cloud
    state = attach_word_cloud(state, room)
    return state


def process_question_end(room):
    room.status = Room.STATUS_REVEAL
    room.save(update_fields=['status'])
    return get_room_state(room)
