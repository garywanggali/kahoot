from __future__ import annotations

import json
import re

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .ai_kahoot import (
    AIKahootError,
    MAX_PER_TYPE,
    MAX_TOTAL_QUESTIONS,
    create_quiz_set_from_ai_data,
    question_type_label,
)
from .stepfun_client import generate_kahoot_questions, stepfun_configured
from .models import (
    Answer,
    Player,
    Question,
    QuizSet,
    Room,
    RoomQuestion,
    Teacher,
    TeacherInviteCode,
)
from .quiz_set_utils import add_question_to_quiz_set, create_room_from_quiz_set
from .teacher_auth import (
    accessible_quiz_sets,
    can_edit_question,
    can_edit_quiz_set,
    can_host_room,
    can_use_quiz_set,
    get_current_teacher,
    login_teacher,
    logout_teacher,
    normalize_username,
    own_quiz_sets,
    public_quiz_sets_excluding,
    require_teacher_or_redirect,
    teacher_rooms,
)
from .room_cache import drop_runtime, flush_runtime_force, get_runtime
from .utils import get_room_state
from .validators import MAX_QUESTION_IMAGE_BYTES, validate_question_image

MIN_TEACHER_PASSWORD_LEN = 6
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,50}$')


def _guard_teacher(request):
    return require_teacher_or_redirect(request)


def index(request):
    return render(request, 'game/index.html')


def join_room(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        nickname = request.POST.get('nickname', '').strip()

        if not code or not nickname:
            messages.error(request, '请输入房间号和昵称')
            return render(request, 'game/join.html')

        try:
            room = Room.objects.get(code=code)
        except Room.DoesNotExist:
            messages.error(request, '房间号不存在')
            return render(request, 'game/join.html', {'code': code, 'nickname': nickname})

        if room.status == Room.STATUS_ENDED:
            messages.error(request, '该房间游戏已结束')
            return render(request, 'game/join.html', {'code': code, 'nickname': nickname})

        request.session['nickname'] = nickname
        request.session['room_code'] = code
        return redirect('play', room_code=code)

    return render(request, 'game/join.html')


def play(request, room_code):
    nickname = request.session.get('nickname')
    if not nickname:
        return redirect('join_room')

    try:
        room = Room.objects.get(code=room_code)
    except Room.DoesNotExist:
        return redirect('index')

    return render(request, 'game/play.html', {
        'room': room,
        'nickname': nickname,
        'initial_state_json': json.dumps(get_room_state(room, runtime=get_runtime(room))),
    })


def teacher_login(request):
    if get_current_teacher(request):
        return redirect('teacher_dashboard')

    if request.method == 'POST':
        username = normalize_username(request.POST.get('username', ''))
        password = request.POST.get('password', '')
        if not username or not password:
            messages.error(request, '请输入用户名和密码')
            return render(request, 'game/teacher_login.html', {'username': username})

        try:
            teacher = Teacher.objects.get(username=username, is_active=True)
        except Teacher.DoesNotExist:
            messages.error(request, '用户名或密码错误')
            return render(request, 'game/teacher_login.html', {'username': username})

        if not teacher.check_password(password):
            messages.error(request, '用户名或密码错误')
            return render(request, 'game/teacher_login.html', {'username': username})

        login_teacher(request, teacher)
        return redirect('teacher_dashboard')

    return render(request, 'game/teacher_login.html')


def teacher_register(request):
    if get_current_teacher(request):
        return redirect('teacher_dashboard')

    ctx = {}
    if request.method == 'POST':
        invite_code = request.POST.get('invite_code', '').strip().upper()
        username_raw = request.POST.get('username', '').strip()
        username = normalize_username(username_raw)
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        ctx = {
            'invite_code': invite_code,
            'username': username_raw,
        }

        if not invite_code:
            messages.error(request, '请输入邀请码')
            return render(request, 'game/teacher_register.html', ctx)

        if not USERNAME_PATTERN.match(username_raw):
            messages.error(request, '用户名须为 3–50 位字母、数字或下划线')
            return render(request, 'game/teacher_register.html', ctx)

        if len(password) < MIN_TEACHER_PASSWORD_LEN:
            messages.error(request, f'密码至少 {MIN_TEACHER_PASSWORD_LEN} 位')
            return render(request, 'game/teacher_register.html', ctx)

        if password != password_confirm:
            messages.error(request, '两次输入的密码不一致')
            return render(request, 'game/teacher_register.html', ctx)

        try:
            invite = TeacherInviteCode.objects.get(code=invite_code)
        except TeacherInviteCode.DoesNotExist:
            messages.error(request, '邀请码无效')
            return render(request, 'game/teacher_register.html', ctx)

        if not invite.can_use():
            messages.error(request, '邀请码已用完或已停用')
            return render(request, 'game/teacher_register.html', ctx)

        if Teacher.objects.filter(username=username).exists():
            messages.error(request, '用户名已被占用')
            return render(request, 'game/teacher_register.html', ctx)

        teacher = Teacher(username=username, display_name=username_raw)
        teacher.set_password(password)
        teacher.save()
        invite.consume()
        login_teacher(request, teacher)
        messages.success(request, f'注册成功，欢迎 {username_raw}！请牢记用户名和密码。')
        return redirect('teacher_dashboard')

    return render(request, 'game/teacher_register.html', ctx)


def teacher_logout(request):
    logout_teacher(request)
    return redirect('index')


def teacher_dashboard(request):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    rooms = teacher_rooms(teacher)[:10]
    quiz_set_count = own_quiz_sets(teacher).count()
    question_count = own_questions(teacher).count()
    return render(request, 'game/teacher_dashboard.html', {
        'rooms': rooms,
        'quiz_set_count': quiz_set_count,
        'question_count': question_count,
        'teacher': teacher,
    })


def question_list(request):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    my_quiz_sets = own_quiz_sets(teacher)
    public_quiz_sets = public_quiz_sets_excluding(teacher)
    return render(request, 'game/question_list.html', {
        'my_quiz_sets': my_quiz_sets,
        'public_quiz_sets': public_quiz_sets,
        'teacher': teacher,
    })


def _get_editable_quiz_set(request, teacher, quiz_set_id):
    if not quiz_set_id:
        return None, None
    quiz_set = get_object_or_404(QuizSet, pk=quiz_set_id)
    if not can_edit_quiz_set(teacher, quiz_set):
        messages.error(request, '无权编辑该套题')
        return None, redirect('question_list')
    return quiz_set, None


def question_create(request):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    quiz_set_id = request.GET.get('quiz_set') or request.POST.get('quiz_set_id')
    quiz_set, quiz_redirect = _get_editable_quiz_set(request, teacher, quiz_set_id)
    if quiz_redirect:
        return quiz_redirect
    if request.method == 'POST':
        return _save_question(request, teacher, quiz_set=quiz_set)
    return render(request, 'game/question_form.html', {
        'action': 'create',
        'max_image_mb': MAX_QUESTION_IMAGE_BYTES // (1024 * 1024),
        'quiz_set': quiz_set,
    })


def question_edit(request, pk):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    question = get_object_or_404(Question, pk=pk)
    if not can_edit_question(teacher, question):
        messages.error(request, '只能编辑自己的题目')
        return redirect('question_list')
    quiz_set = None
    quiz_set_id = request.GET.get('quiz_set') or request.POST.get('quiz_set_id')
    if quiz_set_id:
        quiz_set, quiz_redirect = _get_editable_quiz_set(request, teacher, quiz_set_id)
        if quiz_redirect:
            return quiz_redirect
    if request.method == 'POST':
        return _save_question(request, teacher, question=question, quiz_set=quiz_set)
    return render(request, 'game/question_form.html', {
        'action': 'edit',
        'question': question,
        'max_image_mb': MAX_QUESTION_IMAGE_BYTES // (1024 * 1024),
        'quiz_set': quiz_set,
    })


def question_delete(request, pk):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    question = get_object_or_404(Question, pk=pk)
    if not can_edit_question(teacher, question):
        messages.error(request, '只能删除自己的题目')
        return redirect('question_list')
    quiz_set_id = request.GET.get('quiz_set') or request.POST.get('quiz_set_id')
    if request.method == 'POST':
        question.delete()
        messages.success(request, '题目已删除')
        if quiz_set_id:
            return redirect('kahoot_detail', pk=quiz_set_id)
        return redirect('question_list')
    return render(request, 'game/question_confirm_delete.html', {
        'question': question,
        'quiz_set_id': quiz_set_id,
    })


def _save_question(request, teacher, question=None, quiz_set=None):
    text = request.POST.get('text', '').strip()
    question_type = request.POST.get('question_type', Question.TYPE_SINGLE)
    option_a = request.POST.get('option_a', '').strip()
    option_b = request.POST.get('option_b', '').strip()
    option_c = request.POST.get('option_c', '').strip()
    option_d = request.POST.get('option_d', '').strip()
    time_limit = int(request.POST.get('time_limit', 20) or 20)
    image_file = request.FILES.get('image')
    remove_image = request.POST.get('remove_image') == '1'
    is_public = request.POST.get('is_public') == '1'

    form_ctx = {
        'action': 'edit' if question else 'create',
        'question': question,
        'max_image_mb': MAX_QUESTION_IMAGE_BYTES // (1024 * 1024),
        'quiz_set': quiz_set,
    }

    if question_type not in (
        Question.TYPE_SINGLE, Question.TYPE_MULTIPLE, Question.TYPE_JUDGMENT,
        Question.TYPE_SHORT_ANSWER, Question.TYPE_WORD_CLOUD,
    ):
        question_type = Question.TYPE_SINGLE

    if question_type == Question.TYPE_SHORT_ANSWER:
        option_a = request.POST.get('short_correct', '').strip() or option_a
        if not text or not option_a:
            messages.error(request, '简答题请填写题目和参考答案')
            return render(request, 'game/question_form.html', form_ctx)
        option_b = Question.TEXT_OPTION_PLACEHOLDER
        option_c = Question.TEXT_OPTION_PLACEHOLDER
        option_d = Question.TEXT_OPTION_PLACEHOLDER
        correct_option = 'A'
    elif question_type == Question.TYPE_WORD_CLOUD:
        if not text:
            messages.error(request, '词云题请填写题目')
            return render(request, 'game/question_form.html', form_ctx)
        option_a = Question.TEXT_OPTION_PLACEHOLDER
        option_b = Question.TEXT_OPTION_PLACEHOLDER
        option_c = Question.TEXT_OPTION_PLACEHOLDER
        option_d = Question.TEXT_OPTION_PLACEHOLDER
        correct_option = ''
    elif question_type == Question.TYPE_JUDGMENT:
        if not text or not option_a or not option_b:
            messages.error(request, '判断题请填写题目和正确/错误选项')
            return render(request, 'game/question_form.html', form_ctx)
        option_c = Question.JUDGMENT_OPTION_PLACEHOLDER
        option_d = Question.JUDGMENT_OPTION_PLACEHOLDER
        correct_option = request.POST.get('judgment_correct', 'A').upper()
        if correct_option not in ('A', 'B'):
            correct_option = 'A'
    elif question_type == Question.TYPE_MULTIPLE:
        if not all([text, option_a, option_b, option_c, option_d]):
            messages.error(request, '请填写所有字段')
            return render(request, 'game/question_form.html', form_ctx)
        correct_options = sorted({
            opt.upper() for opt in request.POST.getlist('correct_options')
            if opt.upper() in ('A', 'B', 'C', 'D')
        })
        if len(correct_options) < 2:
            messages.error(request, '多选题请至少选择 2 个正确答案')
            return render(request, 'game/question_form.html', form_ctx)
        correct_option = ','.join(correct_options)
    elif question_type == Question.TYPE_SINGLE:
        if not all([text, option_a, option_b, option_c, option_d]):
            messages.error(request, '请填写所有字段')
            return render(request, 'game/question_form.html', form_ctx)
        correct_option = request.POST.get('correct_option', 'A').upper()
        if correct_option not in ('A', 'B', 'C', 'D'):
            correct_option = 'A'

    if image_file:
        try:
            validate_question_image(image_file)
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return render(request, 'game/question_form.html', form_ctx)

    if question:
        question.text = text
        question.question_type = question_type
        question.option_a = option_a
        question.option_b = option_b
        question.option_c = option_c
        question.option_d = option_d
        question.correct_option = correct_option
        question.time_limit = max(5, min(120, time_limit))
        question.is_public = is_public
        if remove_image and question.image:
            question.image.delete(save=False)
            question.image = None
        if image_file:
            if question.image:
                question.image.delete(save=False)
            question.image = image_file
        question.save()
        messages.success(request, '题目已更新')
        if quiz_set:
            return redirect('kahoot_detail', pk=quiz_set.pk)
    else:
        new_question = Question.objects.create(
            text=text,
            question_type=question_type,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_option,
            time_limit=max(5, min(120, time_limit)),
            image=image_file,
            teacher=teacher,
            is_public=is_public,
        )
        if quiz_set:
            add_question_to_quiz_set(quiz_set, new_question)
        messages.success(request, '题目已创建')
        if quiz_set:
            return redirect('kahoot_detail', pk=quiz_set.pk)

    return redirect('question_list')


def kahoot_new(request):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    pending_title = request.session.pop('kahoot_pending_title', '')
    return render(request, 'game/kahoot_new.html', {
        'quiz_set_count': own_quiz_sets(teacher).count(),
        'pending_title': pending_title,
    })


def kahoot_start(request):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    if request.method != 'POST':
        return redirect('kahoot_new')

    title = request.POST.get('title', '').strip()
    action = request.POST.get('action', '')
    if not title:
        messages.error(request, '请填写 Kahoot 名称')
        request.session['kahoot_pending_title'] = title
        return redirect('kahoot_new')

    if action == 'ai':
        request.session['kahoot_pending_title'] = title
        return redirect('kahoot_ai')

    quiz_set = QuizSet.objects.create(title=title[:200], teacher=teacher)
    messages.success(request, f'已创建「{quiz_set.title}」，请添加题目')
    return redirect('kahoot_detail', pk=quiz_set.pk)


def kahoot_detail(request, pk):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    quiz_set = get_object_or_404(QuizSet, pk=pk)
    can_edit = can_edit_quiz_set(teacher, quiz_set)
    can_use = can_use_quiz_set(teacher, quiz_set)
    if not can_edit and not can_use:
        messages.error(request, '无权查看该套题')
        return redirect('question_list')

    if request.method == 'POST' and can_edit:
        title = request.POST.get('title', '').strip()
        is_public = request.POST.get('is_public') == '1'
        if title:
            quiz_set.title = title[:200]
        quiz_set.is_public = is_public
        quiz_set.save(update_fields=['title', 'is_public'])
        messages.success(request, '套题信息已更新')
        return redirect('kahoot_detail', pk=quiz_set.pk)

    questions = quiz_set.get_questions()
    return render(request, 'game/kahoot_detail.html', {
        'quiz_set': quiz_set,
        'questions': questions,
        'can_edit': can_edit,
        'teacher': teacher,
    })


def kahoot_delete(request, pk):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    quiz_set = get_object_or_404(QuizSet, pk=pk)
    if not can_edit_quiz_set(teacher, quiz_set):
        messages.error(request, '只能删除自己的套题')
        return redirect('question_list')
    if request.method == 'POST':
        title = quiz_set.title
        question_ids = list(
            quiz_set.quiz_set_questions.values_list('question_id', flat=True)
        )
        quiz_set.delete()
        Question.objects.filter(pk__in=question_ids, teacher=teacher).delete()
        messages.success(request, f'已删除套题「{title}」')
        return redirect('question_list')
    return render(request, 'game/kahoot_confirm_delete.html', {'quiz_set': quiz_set})


def kahoot_create_room(request, pk):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    quiz_set = get_object_or_404(QuizSet, pk=pk)
    if not can_use_quiz_set(teacher, quiz_set):
        messages.error(request, '无权使用该套题')
        return redirect('question_list')
    if request.method != 'POST':
        return redirect('kahoot_detail', pk=pk)

    room_name = request.POST.get('name', '').strip()
    try:
        room = create_room_from_quiz_set(quiz_set, teacher, name=room_name)
    except ValueError:
        messages.error(request, '套题中还没有题目，请先添加题目')
        return redirect('kahoot_detail', pk=pk)

    messages.success(request, f'房间已创建，房间号: {room.code}')
    return redirect('room_host', pk=room.pk)


def _parse_ai_counts(request) -> dict[str, int]:
    keys = ('single', 'multiple', 'judgment', 'short_answer')
    counts = {}
    for key in keys:
        try:
            val = int(request.POST.get(f'count_{key}', 0) or 0)
        except ValueError:
            val = 0
        counts[key] = max(0, min(MAX_PER_TYPE, val))
    return counts


def _default_ai_counts() -> dict[str, int]:
    return {
        'single': 3,
        'multiple': 2,
        'judgment': 2,
        'short_answer': 1,
    }


def _ai_form_context(request, **extra):
    counts = extra.get('counts')
    if counts is None:
        counts = _parse_ai_counts(request) if request.method == 'POST' else _default_ai_counts()
    kahoot_title = extra.get('kahoot_title', '')
    if not kahoot_title:
        kahoot_title = request.session.get('kahoot_pending_title', '')
    return {
        'topic': extra.get('topic', request.POST.get('topic', '').strip()),
        'description': extra.get('description', request.POST.get('description', '').strip()),
        'kahoot_title': kahoot_title,
        'counts': counts,
        'ai_configured': stepfun_configured(),
        'max_total': MAX_TOTAL_QUESTIONS,
        'max_per_type': MAX_PER_TYPE,
        **extra,
    }


def kahoot_ai(request):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp

    preview = request.session.get('ai_kahoot_preview')
    kahoot_title = request.session.get('kahoot_pending_title', '')

    if request.method == 'POST' and request.POST.get('action') == 'save':
        if not preview:
            messages.error(request, '没有待保存的题目，请重新生成')
            return render(request, 'game/kahoot_ai.html', _ai_form_context(
                request, kahoot_title=kahoot_title,
            ))

        title = (
            request.session.get('ai_kahoot_title')
            or kahoot_title
            or request.POST.get('kahoot_title', '').strip()
        )
        quiz_set = create_quiz_set_from_ai_data(title, preview, teacher)
        request.session.pop('ai_kahoot_preview', None)
        request.session.pop('ai_kahoot_title', None)
        request.session.pop('kahoot_pending_title', None)
        messages.success(request, f'已保存 {quiz_set.question_count()} 道题到套题「{quiz_set.title}」')
        return redirect('kahoot_detail', pk=quiz_set.pk)

    if request.method == 'POST':
        topic = request.POST.get('topic', '').strip()
        description = request.POST.get('description', '').strip()
        counts = _parse_ai_counts(request)
        total = sum(counts.values())

        if not topic:
            messages.error(request, '请填写主题/方向')
            return render(request, 'game/kahoot_ai.html', _ai_form_context(
                request, counts=counts,
            ))
        if total == 0:
            messages.error(request, '请至少指定 1 道题')
            return render(request, 'game/kahoot_ai.html', _ai_form_context(
                request, counts=counts,
            ))
        if total > MAX_TOTAL_QUESTIONS:
            messages.error(request, f'题目总数不能超过 {MAX_TOTAL_QUESTIONS} 道')
            return render(request, 'game/kahoot_ai.html', _ai_form_context(
                request, counts=counts,
            ))

        try:
            questions = generate_kahoot_questions(topic, description, counts)
        except AIKahootError as e:
            messages.error(request, str(e))
            return render(request, 'game/kahoot_ai.html', _ai_form_context(
                request, counts=counts,
            ))

        request.session['ai_kahoot_preview'] = questions
        request.session['ai_kahoot_title'] = topic
        preview_labels = [
            {**q, 'type_label': question_type_label(q['question_type'])}
            for q in questions
        ]
        messages.success(request, f'已生成 {len(questions)} 道题目，请预览后保存')
        return render(request, 'game/kahoot_ai.html', _ai_form_context(
            request,
            counts=counts,
            preview=preview_labels,
            kahoot_title=kahoot_title or topic,
        ))

    preview_labels = None
    if preview:
        preview_labels = [
            {**q, 'type_label': question_type_label(q['question_type'])}
            for q in preview
        ]

    return render(request, 'game/kahoot_ai.html', _ai_form_context(
        request,
        preview=preview_labels,
        kahoot_title=kahoot_title,
    ))


def kahoot_ai_discard(request):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    if request.method == 'POST':
        request.session.pop('ai_kahoot_preview', None)
        messages.info(request, '已放弃本次 AI 生成结果')
    return redirect('kahoot_ai')


def room_create(request):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    my_sets = own_quiz_sets(teacher)
    public_sets = public_quiz_sets_excluding(teacher)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        quiz_set_id = request.POST.get('quiz_set_id', '').strip()

        if not quiz_set_id:
            messages.error(request, '请选择一套 Kahoot 题目')
            return render(request, 'game/room_create.html', {
                'my_quiz_sets': my_sets,
                'public_quiz_sets': public_sets,
            })

        quiz_set = get_object_or_404(QuizSet, pk=quiz_set_id)
        if not can_use_quiz_set(teacher, quiz_set):
            messages.error(request, '所选套题无效或无权使用')
            return render(request, 'game/room_create.html', {
                'my_quiz_sets': my_sets,
                'public_quiz_sets': public_sets,
            })

        try:
            room = create_room_from_quiz_set(quiz_set, teacher, name=name)
        except ValueError:
            messages.error(request, '该套题还没有题目')
            return render(request, 'game/room_create.html', {
                'my_quiz_sets': my_sets,
                'public_quiz_sets': public_sets,
            })

        messages.success(request, f'房间已创建，房间号: {room.code}')
        return redirect('room_host', pk=room.pk)

    preselect_id = request.GET.get('quiz_set')
    return render(request, 'game/room_create.html', {
        'my_quiz_sets': my_sets,
        'public_quiz_sets': public_sets,
        'preselect_id': preselect_id,
    })


def room_reset(request, pk):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    room = get_object_or_404(Room, pk=pk)
    if not can_host_room(teacher, room):
        messages.error(request, '无权操作该房间')
        return redirect('teacher_dashboard')
    if request.method == 'POST':
        runtime = get_runtime(room)
        flush_runtime_force(runtime)
        drop_runtime(room.code)
        room.status = Room.STATUS_WAITING
        room.current_question_index = -1
        room.question_started_at = None
        room.save(update_fields=['status', 'current_question_index', 'question_started_at'])
        Answer.objects.filter(room=room).delete()
        Player.objects.filter(room=room).update(score=0)
        messages.success(request, '房间已重置')
    return redirect('room_host', pk=pk)


def room_host(request, pk):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    room = get_object_or_404(Room, pk=pk)
    if not can_host_room(teacher, room):
        messages.error(request, '无权主持该房间')
        return redirect('teacher_dashboard')
    questions = room.get_questions()
    return render(request, 'game/room_host.html', {
        'room': room,
        'questions': questions,
        'initial_state_json': json.dumps(get_room_state(room, runtime=get_runtime(room))),
    })


def room_state_api(request, room_code):
    try:
        room = Room.objects.get(code=room_code)
    except Room.DoesNotExist:
        return JsonResponse({'error': '房间不存在'}, status=404)
    runtime = get_runtime(room)
    return JsonResponse(get_room_state(room, runtime=runtime))
