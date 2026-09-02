import json
import re

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .ai_kahoot import (
    AIKahootError,
    MAX_PER_TYPE,
    MAX_TOTAL_QUESTIONS,
    create_questions_from_ai_data,
    question_type_label,
)
from .stepfun_client import generate_kahoot_questions, stepfun_configured
from .models import (
    Answer,
    Player,
    Question,
    Room,
    RoomQuestion,
    Teacher,
    TeacherInviteCode,
)
from .teacher_auth import (
    accessible_questions,
    can_edit_question,
    can_host_room,
    get_current_teacher,
    login_teacher,
    logout_teacher,
    normalize_username,
    own_questions,
    public_questions_excluding,
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
    question_count = own_questions(teacher).count()
    return render(request, 'game/teacher_dashboard.html', {
        'rooms': rooms,
        'question_count': question_count,
        'teacher': teacher,
    })


def question_list(request):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    my_questions = own_questions(teacher)
    public_questions = public_questions_excluding(teacher)
    return render(request, 'game/question_list.html', {
        'my_questions': my_questions,
        'public_questions': public_questions,
        'teacher': teacher,
    })


def question_create(request):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    from_kahoot = request.GET.get('from') == 'kahoot' or request.POST.get('from_kahoot') == '1'
    if request.method == 'POST':
        return _save_question(request, teacher, from_kahoot=from_kahoot)
    return render(request, 'game/question_form.html', {
        'action': 'create',
        'max_image_mb': MAX_QUESTION_IMAGE_BYTES // (1024 * 1024),
        'from_kahoot': from_kahoot,
    })


def question_edit(request, pk):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    question = get_object_or_404(Question, pk=pk)
    if not can_edit_question(teacher, question):
        messages.error(request, '只能编辑自己的题目')
        return redirect('question_list')
    if request.method == 'POST':
        return _save_question(request, teacher, question=question)
    return render(request, 'game/question_form.html', {
        'action': 'edit',
        'question': question,
        'max_image_mb': MAX_QUESTION_IMAGE_BYTES // (1024 * 1024),
    })


def question_delete(request, pk):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    question = get_object_or_404(Question, pk=pk)
    if not can_edit_question(teacher, question):
        messages.error(request, '只能删除自己的题目')
        return redirect('question_list')
    if request.method == 'POST':
        question.delete()
        messages.success(request, '题目已删除')
        return redirect('question_list')
    return render(request, 'game/question_confirm_delete.html', {'question': question})


def _save_question(request, teacher, question=None, from_kahoot=False):
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
        'from_kahoot': from_kahoot,
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
    else:
        Question.objects.create(
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
        messages.success(request, '题目已创建')

    if from_kahoot and not question:
        return redirect(reverse('question_create') + '?from=kahoot')
    return redirect('question_list')


def kahoot_new(request):
    teacher, redirect_resp = require_teacher_or_redirect(request)
    if redirect_resp:
        return redirect_resp
    return render(request, 'game/kahoot_new.html', {
        'question_count': own_questions(teacher).count(),
    })


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
    return {
        'topic': extra.get('topic', request.POST.get('topic', '').strip()),
        'description': extra.get('description', request.POST.get('description', '').strip()),
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

    if request.method == 'POST' and request.POST.get('action') == 'save':
        if not preview:
            messages.error(request, '没有待保存的题目，请重新生成')
            return render(request, 'game/kahoot_ai.html', _ai_form_context(request))

        created = create_questions_from_ai_data(preview, teacher)
        request.session.pop('ai_kahoot_preview', None)
        messages.success(request, f'已保存 {len(created)} 道题目到题库')
        return redirect('question_list')

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
        preview_labels = [
            {**q, 'type_label': question_type_label(q['question_type'])}
            for q in questions
        ]
        messages.success(request, f'已生成 {len(questions)} 道题目，请预览后保存到题库')
        return render(request, 'game/kahoot_ai.html', _ai_form_context(
            request,
            counts=counts,
            preview=preview_labels,
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
    my_qs = own_questions(teacher)
    public_qs = public_questions_excluding(teacher)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        selected_ids = request.POST.getlist('questions')
        allowed_ids = set(accessible_questions(teacher).values_list('pk', flat=True))

        if not selected_ids:
            messages.error(request, '请至少选择一道题目')
            return render(request, 'game/room_create.html', {
                'my_questions': my_qs,
                'public_questions': public_qs,
            })

        if not all(int(qid) in allowed_ids for qid in selected_ids):
            messages.error(request, '所选题目无效或无权使用')
            return render(request, 'game/room_create.html', {
                'my_questions': my_qs,
                'public_questions': public_qs,
            })

        room = Room.objects.create(
            code=Room.generate_code(),
            name=name or '课堂测验',
            teacher=teacher,
        )
        for i, qid in enumerate(selected_ids):
            RoomQuestion.objects.create(
                room=room,
                question_id=qid,
                order=i,
            )
        messages.success(request, f'房间已创建，房间号: {room.code}')
        return redirect('room_host', pk=room.pk)

    return render(request, 'game/room_create.html', {
        'my_questions': my_qs,
        'public_questions': public_qs,
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
