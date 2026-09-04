"""Build word-frequency data for word-cloud questions."""

from .models import Answer, PracticeAttempt, Question, Room
from .room_cache import get_runtime
from .text_utils import normalize_word_cloud_text


def collapse_word_cloud_texts(texts, limit: int = 80) -> list[dict]:
    """Merge equivalents (case / extra spaces) and keep the first display form."""
    buckets: dict[str, dict] = {}
    for raw in texts:
        text = normalize_word_cloud_text(raw or '')
        if not text:
            continue
        key = text.casefold()
        item = buckets.get(key)
        if item is None:
            buckets[key] = {'text': text, 'count': 1}
        else:
            item['count'] += 1
    return sorted(
        buckets.values(),
        key=lambda item: (-item['count'], item['text'].casefold()),
    )[:limit]


def aggregate_word_cloud(room_code: str, question_id: int, runtime=None) -> list[dict]:
    room = Room.objects.get(code=room_code)
    texts: list[str] = []
    flushed_player_ids: set[int] = set()

    for player_id, text in Answer.objects.filter(
        room_id=room.id, question_id=question_id,
    ).values_list('player_id', 'selected_option'):
        if not text:
            continue
        flushed_player_ids.add(player_id)
        texts.append(text)

    if runtime is not None:
        with runtime.lock:
            pending_texts = []
            for pending in runtime.pending_answers:
                if pending.question_id != question_id or not pending.selected:
                    continue
                player = runtime.players.get(pending.session_id)
                if player and player.db_id and player.db_id in flushed_player_ids:
                    continue
                pending_texts.append(pending.selected)
        texts.extend(pending_texts)

    return collapse_word_cloud_texts(texts)


def attach_word_cloud(state: dict, room) -> dict:
    question = state.get('question')
    if not question or question.get('question_type') != Question.TYPE_WORD_CLOUD:
        return state
    runtime = get_runtime(room)
    question['word_cloud'] = aggregate_word_cloud(room.code, question['id'], runtime)
    return state


def aggregate_practice_word_cloud(quiz_set, question_id: int) -> list[dict]:
    texts: list[str] = []
    for answers in PracticeAttempt.objects.filter(quiz_set=quiz_set).values_list('answers', flat=True):
        for item in answers or []:
            if item.get('question_id') != question_id:
                continue
            text = item.get('selected') or ''
            if text:
                texts.append(text)
    return collapse_word_cloud_texts(texts)


def practice_word_clouds(quiz_set) -> list[dict]:
    clouds = []
    for question in quiz_set.get_questions():
        if question.question_type != Question.TYPE_WORD_CLOUD:
            continue
        words = aggregate_practice_word_cloud(quiz_set, question.id)
        clouds.append({
            'question_id': question.id,
            'text': question.text,
            'words': words,
        })
    return clouds
