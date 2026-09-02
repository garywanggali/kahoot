"""Parse and validate question fields from HTTP POST (forms / editor API)."""

from __future__ import annotations

from django.core.exceptions import ValidationError

from .models import Question
from .validators import MAX_QUESTION_IMAGE_BYTES, validate_question_image


class QuestionFormError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def parse_question_from_request(request, question=None) -> dict:
    """Return validated field dict for Question create/update. Raises QuestionFormError."""
    text = request.POST.get('text', '').strip()
    question_type = request.POST.get('question_type', Question.TYPE_SINGLE)
    option_a = request.POST.get('option_a', '').strip()
    option_b = request.POST.get('option_b', '').strip()
    option_c = request.POST.get('option_c', '').strip()
    option_d = request.POST.get('option_d', '').strip()
    try:
        time_limit = int(request.POST.get('time_limit', 20) or 20)
    except ValueError:
        time_limit = 20
    time_limit = max(5, min(120, time_limit))
    is_public = request.POST.get('is_public') == '1'
    image_file = request.FILES.get('image')
    remove_image = request.POST.get('remove_image') == '1'

    if question_type not in (
        Question.TYPE_SINGLE, Question.TYPE_MULTIPLE, Question.TYPE_JUDGMENT,
        Question.TYPE_SHORT_ANSWER, Question.TYPE_WORD_CLOUD,
    ):
        question_type = Question.TYPE_SINGLE

    if question_type == Question.TYPE_SHORT_ANSWER:
        option_a = request.POST.get('short_correct', '').strip() or option_a
        if not text or not option_a:
            raise QuestionFormError('简答题请填写题目和参考答案')
        option_b = Question.TEXT_OPTION_PLACEHOLDER
        option_c = Question.TEXT_OPTION_PLACEHOLDER
        option_d = Question.TEXT_OPTION_PLACEHOLDER
        correct_option = 'A'
    elif question_type == Question.TYPE_WORD_CLOUD:
        if not text:
            raise QuestionFormError('词云题请填写题目')
        option_a = Question.TEXT_OPTION_PLACEHOLDER
        option_b = Question.TEXT_OPTION_PLACEHOLDER
        option_c = Question.TEXT_OPTION_PLACEHOLDER
        option_d = Question.TEXT_OPTION_PLACEHOLDER
        correct_option = ''
    elif question_type == Question.TYPE_JUDGMENT:
        if not text or not option_a or not option_b:
            raise QuestionFormError('判断题请填写题目和正确/错误选项')
        option_c = Question.JUDGMENT_OPTION_PLACEHOLDER
        option_d = Question.JUDGMENT_OPTION_PLACEHOLDER
        correct_option = request.POST.get('judgment_correct', 'A').upper()
        if correct_option not in ('A', 'B'):
            correct_option = 'A'
    elif question_type == Question.TYPE_MULTIPLE:
        if not all([text, option_a, option_b, option_c, option_d]):
            raise QuestionFormError('请填写题目和所有选项')
        correct_options = sorted({
            opt.upper() for opt in request.POST.getlist('correct_options')
            if opt.upper() in ('A', 'B', 'C', 'D')
        })
        if len(correct_options) < 2:
            raise QuestionFormError('多选题请至少选择 2 个正确答案')
        correct_option = ','.join(correct_options)
    else:
        if not all([text, option_a, option_b, option_c, option_d]):
            raise QuestionFormError('请填写题目和所有选项')
        correct_option = request.POST.get('correct_option', 'A').upper()
        if correct_option not in ('A', 'B', 'C', 'D'):
            correct_option = 'A'

    if image_file:
        try:
            validate_question_image(image_file)
        except ValidationError as exc:
            raise QuestionFormError(exc.messages[0])

    return {
        'text': text,
        'question_type': question_type,
        'option_a': option_a,
        'option_b': option_b,
        'option_c': option_c,
        'option_d': option_d,
        'correct_option': correct_option,
        'time_limit': time_limit,
        'is_public': is_public,
        'image_file': image_file,
        'remove_image': remove_image,
    }


def apply_question_fields(question: Question, fields: dict) -> None:
    question.text = fields['text']
    question.question_type = fields['question_type']
    question.option_a = fields['option_a']
    question.option_b = fields['option_b']
    question.option_c = fields['option_c']
    question.option_d = fields['option_d']
    question.correct_option = fields['correct_option']
    question.time_limit = fields['time_limit']
    question.is_public = fields['is_public']
    if fields['remove_image'] and question.image:
        question.image.delete(save=False)
        question.image = None
    if fields['image_file']:
        if question.image:
            question.image.delete(save=False)
        question.image = fields['image_file']


def question_to_editor_dict(question: Question) -> dict:
    data = {
        'id': question.pk,
        'text': question.text,
        'question_type': question.question_type,
        'option_a': question.option_a,
        'option_b': question.option_b,
        'option_c': question.option_c,
        'option_d': question.option_d,
        'correct_option': question.correct_option,
        'correct_option_keys': question.correct_option_keys,
        'time_limit': question.time_limit,
        'is_public': question.is_public,
        'image_url': question.image.url if question.image else '',
    }
    if question.question_type == Question.TYPE_SHORT_ANSWER:
        data['short_correct'] = question.option_a
    return data
