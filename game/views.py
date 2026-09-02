import json

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Answer, Player, Question, Room, RoomQuestion
from .utils import get_room_state
from .validators import MAX_QUESTION_IMAGE_BYTES, validate_question_image


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
        'initial_state_json': json.dumps(get_room_state(room)),
    })


def teacher_login(request):
    if request.method == 'POST':
        password = request.POST.get('password', '')
        if password == settings.TEACHER_PASSWORD:
            request.session['is_teacher'] = True
            return redirect('teacher_dashboard')
        messages.error(request, '密码错误')
    return render(request, 'game/teacher_login.html')


def teacher_logout(request):
    request.session.pop('is_teacher', None)
    return redirect('index')


def _require_teacher(request):
    if not request.session.get('is_teacher'):
        return redirect('teacher_login')
    return None


def teacher_dashboard(request):
    if _require_teacher(request):
        return _require_teacher(request)
    rooms = Room.objects.all()[:10]
    question_count = Question.objects.count()
    return render(request, 'game/teacher_dashboard.html', {
        'rooms': rooms,
        'question_count': question_count,
    })


def question_list(request):
    if _require_teacher(request):
        return _require_teacher(request)
    questions = Question.objects.all()
    return render(request, 'game/question_list.html', {'questions': questions})


def question_create(request):
    if _require_teacher(request):
        return _require_teacher(request)
    if request.method == 'POST':
        return _save_question(request)
    return render(request, 'game/question_form.html', {
        'action': 'create',
        'max_image_mb': MAX_QUESTION_IMAGE_BYTES // (1024 * 1024),
    })


def question_edit(request, pk):
    if _require_teacher(request):
        return _require_teacher(request)
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        return _save_question(request, question)
    return render(request, 'game/question_form.html', {
        'action': 'edit',
        'question': question,
        'max_image_mb': MAX_QUESTION_IMAGE_BYTES // (1024 * 1024),
    })


def question_delete(request, pk):
    if _require_teacher(request):
        return _require_teacher(request)
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        question.delete()
        messages.success(request, '题目已删除')
        return redirect('question_list')
    return render(request, 'game/question_confirm_delete.html', {'question': question})


def _save_question(request, question=None):
    text = request.POST.get('text', '').strip()
    question_type = request.POST.get('question_type', Question.TYPE_SINGLE)
    option_a = request.POST.get('option_a', '').strip()
    option_b = request.POST.get('option_b', '').strip()
    option_c = request.POST.get('option_c', '').strip()
    option_d = request.POST.get('option_d', '').strip()
    time_limit = int(request.POST.get('time_limit', 20) or 20)
    image_file = request.FILES.get('image')
    remove_image = request.POST.get('remove_image') == '1'

    form_ctx = {
        'action': 'edit' if question else 'create',
        'question': question,
        'max_image_mb': MAX_QUESTION_IMAGE_BYTES // (1024 * 1024),
    }

    if not all([text, option_a, option_b, option_c, option_d]):
        messages.error(request, '请填写所有字段')
        return render(request, 'game/question_form.html', form_ctx)

    if question_type not in (Question.TYPE_SINGLE, Question.TYPE_MULTIPLE):
        question_type = Question.TYPE_SINGLE

    if question_type == Question.TYPE_MULTIPLE:
        correct_options = sorted({
            opt.upper() for opt in request.POST.getlist('correct_options')
            if opt.upper() in ('A', 'B', 'C', 'D')
        })
        if len(correct_options) < 2:
            messages.error(request, '多选题请至少选择 2 个正确答案')
            return render(request, 'game/question_form.html', form_ctx)
        correct_option = ','.join(correct_options)
    else:
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
        )
        messages.success(request, '题目已创建')

    return redirect('question_list')


def room_create(request):
    if _require_teacher(request):
        return _require_teacher(request)
    questions = Question.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        selected_ids = request.POST.getlist('questions')

        if not selected_ids:
            messages.error(request, '请至少选择一道题目')
            return render(request, 'game/room_create.html', {'questions': questions})

        room = Room.objects.create(
            code=Room.generate_code(),
            name=name or '课堂测验',
        )
        for i, qid in enumerate(selected_ids):
            RoomQuestion.objects.create(
                room=room,
                question_id=qid,
                order=i,
            )
        messages.success(request, f'房间已创建，房间号: {room.code}')
        return redirect('room_host', pk=room.pk)

    return render(request, 'game/room_create.html', {'questions': questions})


def room_reset(request, pk):
    if _require_teacher(request):
        return _require_teacher(request)
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.status = Room.STATUS_WAITING
        room.current_question_index = -1
        room.question_started_at = None
        room.save(update_fields=['status', 'current_question_index', 'question_started_at'])
        Answer.objects.filter(room=room).delete()
        Player.objects.filter(room=room).update(score=0)
        messages.success(request, '房间已重置')
    return redirect('room_host', pk=pk)


def room_host(request, pk):
    if _require_teacher(request):
        return _require_teacher(request)
    room = get_object_or_404(Room, pk=pk)
    questions = room.get_questions()
    return render(request, 'game/room_host.html', {
        'room': room,
        'questions': questions,
        'initial_state_json': json.dumps(get_room_state(room)),
    })


def room_state_api(request, room_code):
    try:
        room = Room.objects.get(code=room_code)
    except Room.DoesNotExist:
        return JsonResponse({'error': '房间不存在'}, status=404)
    return JsonResponse(get_room_state(room))
