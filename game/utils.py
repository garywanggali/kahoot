from django.utils import timezone

from .models import Answer, Player, Question, Room
from .validators import MAX_QUESTION_IMAGE_BYTES


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
        {'nickname': p.nickname, 'score': p.score, 'rank': i + 1}
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
    }
    if current_q and room.status in (Room.STATUS_PLAYING, Room.STATUS_LEADERBOARD):
        question_data = {
            'id': current_q.id,
            'text': current_q.text,
            'question_type': current_q.question_type,
            'options': current_q.get_options(),
            'time_limit': current_q.time_limit,
        }
        if room.status == Room.STATUS_LEADERBOARD:
            if current_q.question_type == Question.TYPE_MULTIPLE:
                question_data['correct_options'] = sorted(current_q.get_correct_option_set())
            elif current_q.question_type == Question.TYPE_JUDGMENT:
                key = current_q.correct_option.strip().upper()
                question_data['correct_option'] = (
                    current_q.option_a if key == 'A' else current_q.option_b
                )
            else:
                question_data['correct_option'] = current_q.correct_option
        if current_q.image:
            question_data['image_url'] = current_q.image.url
        state['question'] = question_data
    if runtime is not None:
        from .room_cache import overlay_room_state
        state = overlay_room_state(state, runtime)
    return state


def process_question_end(room):
    room.status = Room.STATUS_LEADERBOARD
    room.save(update_fields=['status'])
    return get_room_state(room)
