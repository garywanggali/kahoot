from django.utils import timezone

from .models import Answer, Player, Room


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


def get_room_state(room):
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
        state['question'] = {
            'id': current_q.id,
            'text': current_q.text,
            'options': current_q.get_options(),
            'time_limit': current_q.time_limit,
            'correct_option': current_q.correct_option if room.status == Room.STATUS_LEADERBOARD else None,
        }
    return state


def process_question_end(room):
    room.status = Room.STATUS_LEADERBOARD
    room.save(update_fields=['status'])
    return get_room_state(room)
