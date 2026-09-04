"""Teacher session auth and question access helpers."""

from __future__ import annotations

import re

from django.db.models import Q
from django.shortcuts import redirect

from .models import Question, QuizSet, Room, Teacher


SESSION_TEACHER_KEY = 'teacher_id'
MIN_TEACHER_PASSWORD_LEN = 6
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,50}$')
TEACHER_GENDERS = {
    Teacher.GENDER_UNSPECIFIED,
    Teacher.GENDER_FEMALE,
    Teacher.GENDER_MALE,
    Teacher.GENDER_OTHER,
}


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


def require_teacher_api(request):
    """For JSON API views: return 401 instead of HTML redirect."""
    from django.http import JsonResponse

    teacher = get_current_teacher(request)
    if not teacher:
        return None, JsonResponse({'error': '请先登录老师账号'}, status=401)
    return teacher, None


def normalize_username(username: str) -> str:
    return username.strip().lower()


def apply_teacher_settings(teacher: Teacher, payload: dict) -> tuple[Teacher | None, str | None]:
    """Update profile fields. Returns (teacher, error_message)."""
    display_name = str(payload.get('display_name') or '').strip()[:100]
    gender = str(payload.get('gender') or Teacher.GENDER_UNSPECIFIED).strip()
    if gender not in TEACHER_GENDERS:
        gender = Teacher.GENDER_UNSPECIFIED

    avatar_payload = payload.get('avatar')
    if not isinstance(avatar_payload, dict):
        avatar_payload = {
            'face': payload.get('avatar_face', payload.get('face', 0)),
            'hair': payload.get('avatar_hair', payload.get('hair', 0)),
            'acc': payload.get('avatar_acc', payload.get('acc', 0)),
        }

    username_raw = str(payload.get('username') or teacher.username).strip()
    new_username = normalize_username(username_raw)
    current_password = str(payload.get('current_password') or '')
    new_password = str(payload.get('new_password') or '')
    new_password_confirm = str(payload.get('new_password_confirm') or '')

    username_changed = new_username != teacher.username
    password_changed = bool(new_password)

    if username_changed:
        if not USERNAME_PATTERN.match(username_raw):
            return None, '用户名须为 3–50 位字母、数字或下划线'
        if not current_password or not teacher.check_password(current_password):
            return None, '更改用户名请输入当前密码'
        taken = Teacher.objects.filter(username=new_username).exclude(pk=teacher.pk).exists()
        if taken:
            return None, '用户名已被占用'

    if password_changed:
        if not current_password or not teacher.check_password(current_password):
            return None, '更改密码请输入当前密码'
        if len(new_password) < MIN_TEACHER_PASSWORD_LEN:
            return None, f'新密码至少 {MIN_TEACHER_PASSWORD_LEN} 位'
        if new_password != new_password_confirm:
            return None, '两次输入的新密码不一致'

    teacher.display_name = display_name
    teacher.gender = gender
    teacher.set_avatar_dict(avatar_payload)
    update_fields = ['display_name', 'gender', 'avatar']
    if username_changed:
        teacher.username = new_username
        update_fields.append('username')
    if password_changed:
        teacher.set_password(new_password)
        update_fields.append('password_hash')
    teacher.save(update_fields=update_fields)
    return teacher, None


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


def own_quiz_sets(teacher: Teacher):
    return QuizSet.objects.filter(teacher=teacher)


def accessible_quiz_sets(teacher: Teacher):
    """Own quiz sets + public sets from other teachers."""
    return QuizSet.objects.filter(
        Q(teacher=teacher) | Q(is_public=True),
    ).select_related('teacher').order_by('-created_at')


def _filter_quiz_sets_by_search(qs, search: str = ''):
    term = (search or '').strip()
    if not term:
        return qs
    return qs.filter(
        Q(title__icontains=term)
        | Q(teacher__username__icontains=term)
        | Q(teacher__display_name__icontains=term)
        | Q(quiz_set_questions__question__text__icontains=term)
        | Q(quiz_set_questions__question__option_a__icontains=term)
        | Q(quiz_set_questions__question__option_b__icontains=term)
        | Q(quiz_set_questions__question__option_c__icontains=term)
        | Q(quiz_set_questions__question__option_d__icontains=term)
        | Q(practice_code__icontains=term)
    ).distinct()


def public_quiz_sets_excluding(teacher: Teacher, search: str = ''):
    qs = QuizSet.objects.filter(is_public=True).exclude(
        teacher=teacher,
    ).select_related('teacher')
    return _filter_quiz_sets_by_search(qs, search).order_by('-created_at')


def all_public_quiz_sets(search: str = ''):
    qs = QuizSet.objects.filter(is_public=True).select_related('teacher')
    return _filter_quiz_sets_by_search(qs, search).order_by('-created_at')


def can_edit_quiz_set(teacher: Teacher, quiz_set: QuizSet) -> bool:
    return quiz_set.teacher_id == teacher.pk


def can_use_quiz_set(teacher: Teacher, quiz_set: QuizSet) -> bool:
    if quiz_set.teacher_id == teacher.pk:
        return True
    return quiz_set.is_public
