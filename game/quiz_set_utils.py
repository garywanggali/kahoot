"""Quiz set (Kahoot bundle) helpers."""

from __future__ import annotations

from django.db import transaction

from .models import Question, QuizSet, QuizSetQuestion, Room, RoomQuestion


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


@transaction.atomic
def clone_quiz_set(source: QuizSet, teacher, title: str | None = None) -> QuizSet:
    new_title = (title or '').strip() or f'{source.title}（副本）'
    new_set = QuizSet.objects.create(
        title=new_title[:200],
        teacher=teacher,
        is_public=False,
    )
    for qsq in source.quiz_set_questions.select_related('question').order_by('order'):
        q = qsq.question
        new_q = Question.objects.create(
            text=q.text,
            question_type=q.question_type,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            correct_option=q.correct_option,
            time_limit=q.time_limit,
            teacher=teacher,
            is_public=False,
        )
        if q.image:
            # 图片不复制，避免跨教师 media 权限问题
            pass
        QuizSetQuestion.objects.create(
            quiz_set=new_set,
            question=new_q,
            order=qsq.order,
        )
    return new_set
