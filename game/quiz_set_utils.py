"""Quiz set (Kahoot bundle) helpers."""

from __future__ import annotations

from .models import QuizSet, QuizSetQuestion, Room, RoomQuestion


def create_room_from_quiz_set(quiz_set: QuizSet, teacher, name: str | None = None) -> Room:
    questions = quiz_set.get_questions()
    if not questions:
        raise ValueError('套题中没有题目')

    room = Room.objects.create(
        code=Room.generate_code(),
        name=(name or '').strip() or quiz_set.title or '课堂测验',
        teacher=teacher,
        source_quiz_set=quiz_set,
    )
    for order, question in enumerate(questions):
        RoomQuestion.objects.create(
            room=room,
            question=question,
            order=order,
        )
    return room


def add_question_to_quiz_set(quiz_set: QuizSet, question, order: int | None = None) -> QuizSetQuestion:
    if order is None:
        last = quiz_set.quiz_set_questions.order_by('-order').first()
        order = (last.order + 1) if last else 0
    return QuizSetQuestion.objects.create(
        quiz_set=quiz_set,
        question=question,
        order=order,
    )
