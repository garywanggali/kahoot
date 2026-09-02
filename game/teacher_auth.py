"""Teacher session auth and question access helpers."""

from __future__ import annotations

from django.db.models import Q
from django.shortcuts import redirect

from .models import Question, Room, Teacher


SESSION_TEACHER_KEY = 'teacher_id'


def get_current_teacher(request) -> Teacher | None:
    teacher_id = request.session.get(SESSION_TEACHER_KEY)
    if not teacher_id:
        return None
    try:
        return Teacher.objects.get(pk=teacher_id, is_active=True)
    except Teacher.DoesNotExist:
        return None


def login_teacher(request, teacher: Teacher) -> None:
    request.session[SESSION_TEACHER_KEY] = teacher.pk
    request.session.pop('is_teacher', None)


def logout_teacher(request) -> None:
    request.session.pop(SESSION_TEACHER_KEY, None)
    request.session.pop('is_teacher', None)


def require_teacher_or_redirect(request):
    teacher = get_current_teacher(request)
    if not teacher:
        return None, redirect('teacher_login')
    return teacher, None


def normalize_username(username: str) -> str:
    return username.strip().lower()


def own_questions(teacher: Teacher):
    return Question.objects.filter(teacher=teacher)


def accessible_questions(teacher: Teacher):
    """Questions the teacher can use in rooms: own + public from others."""
    return Question.objects.filter(
        Q(teacher=teacher) | Q(is_public=True),
    ).select_related('teacher').order_by('-created_at')


def public_questions_excluding(teacher: Teacher):
    return Question.objects.filter(is_public=True).exclude(
        teacher=teacher,
    ).select_related('teacher').order_by('-created_at')


def teacher_rooms(teacher: Teacher):
    return Room.objects.filter(teacher=teacher).order_by('-created_at')


def can_edit_question(teacher: Teacher, question: Question) -> bool:
    return question.teacher_id == teacher.pk


def can_host_room(teacher: Teacher, room: Room) -> bool:
    if room.teacher_id is None:
        return True
    return room.teacher_id == teacher.pk
