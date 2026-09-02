"""Build word-frequency data for word-cloud questions."""

from collections import Counter

from .models import Answer, Question
from .room_cache import get_runtime
from .text_utils import normalize_word_cloud_text


def aggregate_word_cloud(room_id: int, question_id: int, runtime=None) -> list[dict]:
    counts: Counter[str] = Counter()

    if runtime is not None:
        with runtime.lock:
            pending_texts = [
                pending.selected
                for pending in runtime.pending_answers
                if pending.question_id == question_id and pending.selected
            ]
        for text in pending_texts:
            counts[text] += 1

    for text in Answer.objects.filter(
        room_id=room_id, question_id=question_id,
    ).values_list('selected_option', flat=True):
        if text:
            counts[text] += 1

    return [
        {'text': word, 'count': count}
        for word, count in counts.most_common(80)
    ]


def attach_word_cloud(state: dict, room) -> dict:
    question = state.get('question')
    if not question or question.get('question_type') != Question.TYPE_WORD_CLOUD:
        return state
    runtime = get_runtime(room)
    question['word_cloud'] = aggregate_word_cloud(room.id, question['id'], runtime)
    return state
