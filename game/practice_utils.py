"""Solo practice mode for public quiz sets (6-letter codes)."""

from __future__ import annotations

import json
import random
import re
import secrets

from django.db.models import Q
from django.utils import timezone

from .models import PracticeAttempt, Question, QuizSet, _parse_avatar_json
from .question_save import _question_image_url
from .text_utils import normalize_word_cloud_text
from .utils import calculate_points

PRACTICE_CODE_LENGTH = 6
# Skip I/O so letter codes are not confused with digit PINs 1/0.
PRACTICE_CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
JOIN_CODE_RE = re.compile(r'^[A-Za-z0-9]{6}$')


def normalize_join_code(raw: str) -> str:
    return (raw or '').strip().replace(' ', '').upper()


def classify_join_code(raw: str) -> tuple[str, str]:
    """Return ('pin'|'practice'|'invalid', normalized_code)."""
    code = normalize_join_code(raw)
    if not JOIN_CODE_RE.match(code):
        return 'invalid', code
    if code.isdigit():
        return 'pin', code
    if code.isalpha():
        return 'practice', code
    return 'invalid', code


def generate_practice_code() -> str:
    while True:
        code = ''.join(random.choices(PRACTICE_CODE_ALPHABET, k=PRACTICE_CODE_LENGTH))
        if not QuizSet.objects.filter(practice_code=code).exists():
            return code


def ensure_practice_code(quiz_set: QuizSet) -> str:
    if quiz_set.practice_code:
        return quiz_set.practice_code
    quiz_set.practice_code = generate_practice_code()
    quiz_set.save(update_fields=['practice_code'])
    return quiz_set.practice_code


def assign_missing_practice_codes() -> int:
    assigned = 0
    missing = QuizSet.objects.filter(is_public=True).filter(
        Q(practice_code__isnull=True) | Q(practice_code=''),
    )
    for quiz_set in missing:
        ensure_practice_code(quiz_set)
        assigned += 1
    return assigned


def get_public_quiz_by_practice_code(code: str) -> QuizSet | None:
    kind, normalized = classify_join_code(code)
    if kind != 'practice':
        return None
    return QuizSet.objects.filter(
        is_public=True,
        practice_code=normalized,
    ).select_related('teacher').first()


def serialize_practice_question(question: Question) -> dict:
    payload = {
        'id': question.id,
        'text': question.text,
        'question_type': question.question_type,
        'options': question.get_options(),
        # Practice mode is untimed: keep time_limit for display/scoring ratio only.
        'time_limit': int(question.time_limit or 0),
        'no_score': question.question_type in Question.UNSCORED_TYPES,
        'uses_countdown': False,
    }
    if question.image:
        payload['image_url'] = _question_image_url(question)
    return payload


def serialize_practice_quiz(quiz_set: QuizSet) -> dict:
    questions = quiz_set.get_questions()
    return {
        'title': quiz_set.title,
        'practice_code': quiz_set.practice_code,
        'author': quiz_set.teacher.display_name or quiz_set.teacher.username,
        'total_questions': len(questions),
        'countdown_seconds': 0,
        'questions': [serialize_practice_question(q) for q in questions],
    }


def score_practice_answer(question: Question, selected: str, response_time_ms: int) -> tuple[bool, int]:
    selected = selected or ''
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


def _json_avatar(avatar) -> str:
    parsed = _parse_avatar_json(avatar)
    return json.dumps(parsed, separators=(',', ':'))


def create_practice_attempt(quiz_set: QuizSet, nickname: str, avatar=None) -> PracticeAttempt:
    return PracticeAttempt.objects.create(
        quiz_set=quiz_set,
        nickname=(nickname or '').strip()[:50],
        token=secrets.token_hex(16),
        avatar=_json_avatar(avatar),
    )


def record_practice_answer(
    attempt: PracticeAttempt,
    question: Question,
    selected: str,
    response_time_ms: int,
) -> dict:
    if attempt.finished_at:
        raise ValueError('练习已结束')
    answers = list(attempt.answers or [])
    if any(item.get('question_id') == question.id for item in answers):
        raise ValueError('本题已经作答')
    owned_ids = {q.id for q in attempt.quiz_set.get_questions()}
    if question.id not in owned_ids:
        raise ValueError('题目不属于该套题')

    if question.question_type == Question.TYPE_WORD_CLOUD:
        selected = normalize_word_cloud_text(selected or '')
        if not selected:
            raise ValueError('请输入一个词')

    is_correct, points = score_practice_answer(
        question, selected, max(0, int(response_time_ms or 0)),
    )
    answers.append({
        'question_id': question.id,
        'selected': selected,
        'is_correct': is_correct,
        'points': points,
    })
    attempt.answers = answers
    attempt.score = sum(int(item.get('points') or 0) for item in answers)
    attempt.save(update_fields=['answers', 'score'])
    return {
        'is_correct': is_correct,
        'points': points,
        'score': attempt.score,
        'no_score': question.question_type in Question.UNSCORED_TYPES,
    }


def finish_practice_attempt(attempt: PracticeAttempt) -> PracticeAttempt:
    if not attempt.finished_at:
        attempt.finished_at = timezone.now()
        attempt.save(update_fields=['finished_at', 'score'])
    return attempt


def practice_leaderboard(quiz_set: QuizSet, limit: int = 50) -> list[dict]:
    rows = PracticeAttempt.objects.filter(
        quiz_set=quiz_set,
        finished_at__isnull=False,
    ).order_by('-score', 'finished_at', 'pk')
    seen = set()
    board = []
    for attempt in rows:
        key = (attempt.nickname or '').strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        board.append({
            'nickname': attempt.nickname,
            'score': attempt.score,
            'rank': len(board) + 1,
            'avatar': attempt.get_avatar_dict(),
        })
        if len(board) >= limit:
            break
    return board
