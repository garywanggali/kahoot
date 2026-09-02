"""Shared AI Kahoot prompt building, validation, and persistence."""

from __future__ import annotations

import json

from django.db import transaction

from .models import Question, QuizSet
from .quiz_set_utils import add_question_to_quiz_set

MAX_TOTAL_QUESTIONS = 30
MAX_PER_TYPE = 20
MAX_AI_SHORT_ANSWER_LEN = 20
_SHORT_ANSWER_MULTI_ITEM_MARKERS = ('和', '与', '及', '、')

QUESTION_JSON_SCHEMA = {
    'type': 'object',
    'properties': {
        'questions': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'question_type': {
                        'type': 'string',
                        'enum': ['single', 'multiple', 'judgment', 'short_answer'],
                    },
                    'text': {'type': 'string'},
                    'option_a': {'type': 'string'},
                    'option_b': {'type': 'string'},
                    'option_c': {'type': 'string'},
                    'option_d': {'type': 'string'},
                    'correct_option': {'type': 'string'},
                    'time_limit': {'type': 'integer'},
                },
                'required': [
                    'question_type', 'text', 'option_a', 'option_b',
                    'option_c', 'option_d', 'correct_option', 'time_limit',
                ],
            },
        },
    },
    'required': ['questions'],
}


class AIKahootError(Exception):
    """Raised when AI generation or validation fails."""


def _short_answer_looks_like_multi_item_list(text: str) -> bool:
    if any(marker in text for marker in _SHORT_ANSWER_MULTI_ITEM_MARKERS):
        return True
    return '，' in text or ',' in text


def is_valid_ai_short_answer(option_a: str) -> bool:
    """Reject AI short answers that are hard to auto-match."""
    if not option_a or not option_a.strip():
        return False
    if any(ch.isspace() for ch in option_a):
        return False
    segments = [part.strip() for part in option_a.split('|') if part.strip()]
    if not segments:
        return False
    for segment in segments:
        if any(ch.isspace() for ch in segment):
            return False
        if len(segment) > MAX_AI_SHORT_ANSWER_LEN:
            return False
        if _short_answer_looks_like_multi_item_list(segment):
            return False
    return True


def build_system_prompt() -> str:
    schema_text = json.dumps(QUESTION_JSON_SCHEMA, ensure_ascii=False, indent=2)
    return (
        '你是一位资深教师，正在为课堂互动测验（类似 Kahoot）批量出题。'
        '你必须只输出一个 JSON 对象，不要输出 Markdown 或其它说明文字。'
        'JSON 结构必须符合下列 JSON Schema：\n'
        f'{schema_text}\n\n'
        '字段规则：\n'
        '- question_type 只能是 single、multiple、judgment、short_answer。\n'
        '- 多选题 correct_option 为逗号分隔字母，如 A,C，至少 2 个正确答案。\n'
        '- 判断题 option_a 为「正确」，option_b 为「错误」，correct_option 为 A 或 B。\n'
        '- 简答题参考答案写在 option_a，correct_option 固定 A；option_b/option_c/option_d 可写「—」。\n'
        '- 简答题必须便于系统自动判分：参考答案只能是极短的词或数字（通常几个字，如 北京、1949、'
        '二氧化碳），不得含空格。\n'
        '- 禁止简答题答案为多个并列项（如「德国和日本」）或含「和」「与」「及」、顿号、逗号的列举；'
        '此类应改为单选题或多选题。\n'
        '- 若同一答案有多种简短写法，仅用 | 分隔（如 二氧化碳|CO2），且每种写法都必须无空格、'
        f'不超过 {MAX_AI_SHORT_ANSWER_LEN} 个字符。\n'
        '- 简答题题干应要求单个简短答案，避免「列举…」「说出两个…」等需多个词或多项的作答方式。\n'
        '- 题目使用简体中文，难度适合中学生。\n'
        '- 不要生成词云题。'
    )


def build_user_prompt(topic: str, description: str, counts: dict[str, int]) -> str:
    lines = [
        f'主题/方向：{topic}',
    ]
    if description.strip():
        lines.append(f'额外要求与限制：{description.strip()}')
    lines.extend([
        '',
        '各题型数量（必须严格等于下列数量）：',
        f'- 单选题 (single)：{counts["single"]} 道',
        f'- 多选题 (multiple)：{counts["multiple"]} 道',
        f'- 判断题 (judgment)：{counts["judgment"]} 道',
        f'- 简答题 (short_answer)：{counts["short_answer"]} 道',
        '',
        '请生成题目并输出 JSON。',
    ])
    return '\n'.join(lines)


def validate_and_normalize_questions(
    raw_questions: list,
    expected_counts: dict[str, int],
) -> list[dict]:
    if not isinstance(raw_questions, list):
        raise AIKahootError('AI 未返回题目列表')

    normalized = []
    for item in raw_questions:
        if not isinstance(item, dict):
            continue
        qtype = item.get('question_type', '')
        if qtype not in (
            Question.TYPE_SINGLE, Question.TYPE_MULTIPLE,
            Question.TYPE_JUDGMENT, Question.TYPE_SHORT_ANSWER,
        ):
            continue

        text = str(item.get('text', '')).strip()
        if not text:
            continue

        option_a = str(item.get('option_a', '')).strip()
        option_b = str(item.get('option_b', '')).strip()
        option_c = str(item.get('option_c', '')).strip()
        option_d = str(item.get('option_d', '')).strip()
        correct = str(item.get('correct_option', '')).strip().upper()
        time_limit = int(item.get('time_limit', 20) or 20)
        time_limit = max(5, min(120, time_limit))

        if qtype == Question.TYPE_JUDGMENT:
            option_a = option_a or '正确'
            option_b = option_b or '错误'
            option_c = Question.JUDGMENT_OPTION_PLACEHOLDER
            option_d = Question.JUDGMENT_OPTION_PLACEHOLDER
            if correct not in ('A', 'B'):
                correct = 'A'
        elif qtype == Question.TYPE_SHORT_ANSWER:
            if not is_valid_ai_short_answer(option_a):
                continue
            option_b = Question.TEXT_OPTION_PLACEHOLDER
            option_c = Question.TEXT_OPTION_PLACEHOLDER
            option_d = Question.TEXT_OPTION_PLACEHOLDER
            correct = 'A'
        elif qtype == Question.TYPE_MULTIPLE:
            keys = sorted({c for c in correct.replace(',', '') if c in ('A', 'B', 'C', 'D')})
            if len(keys) < 2 or not all([option_a, option_b, option_c, option_d]):
                continue
            correct = ','.join(keys)
        elif qtype == Question.TYPE_SINGLE:
            if correct not in ('A', 'B', 'C', 'D'):
                correct = 'A'
            if not all([option_a, option_b, option_c, option_d]):
                continue

        normalized.append({
            'question_type': qtype,
            'text': text[:500],
            'option_a': option_a[:200],
            'option_b': option_b[:200],
            'option_c': option_c[:200],
            'option_d': option_d[:200],
            'correct_option': correct[:10],
            'time_limit': time_limit,
        })

    expected_total = sum(expected_counts.values())
    if len(normalized) < expected_total:
        raise AIKahootError(
            f'AI 仅生成了 {len(normalized)} 道有效题目（期望 {expected_total} 道），请重试。'
        )

    return normalized


def create_questions_from_ai_data(items: list[dict], teacher) -> list[Question]:
    created = []
    for item in items:
        q = Question.objects.create(
            text=item['text'],
            question_type=item['question_type'],
            option_a=item['option_a'],
            option_b=item['option_b'],
            option_c=item['option_c'],
            option_d=item['option_d'],
            correct_option=item['correct_option'],
            time_limit=item['time_limit'],
            teacher=teacher,
            is_public=False,
        )
        created.append(q)
    return created


@transaction.atomic
def create_quiz_set_from_ai_data(title: str, items: list[dict], teacher) -> QuizSet:
    title = (title or '').strip() or 'AI 生成测验'
    quiz_set = QuizSet.objects.create(
        title=title[:200],
        teacher=teacher,
        is_public=False,
    )
    for order, item in enumerate(items):
        question = Question.objects.create(
            text=item['text'],
            question_type=item['question_type'],
            option_a=item['option_a'],
            option_b=item['option_b'],
            option_c=item['option_c'],
            option_d=item['option_d'],
            correct_option=item['correct_option'],
            time_limit=item['time_limit'],
            teacher=teacher,
            is_public=False,
        )
        add_question_to_quiz_set(quiz_set, question, order=order)
    return quiz_set


def question_type_label(qtype: str) -> str:
    labels = {
        Question.TYPE_SINGLE: '单选',
        Question.TYPE_MULTIPLE: '多选',
        Question.TYPE_JUDGMENT: '判断',
        Question.TYPE_SHORT_ANSWER: '简答',
        Question.TYPE_WORD_CLOUD: '词云',
    }
    return labels.get(qtype, '单选')
