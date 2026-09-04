"""阶跃星辰 StepFun API client (OpenAI-compatible Chat Completions)."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request

from django.conf import settings

from .ai_shoot import (
    AIShootError,
    MAX_PER_TYPE,
    MAX_TOTAL_QUESTIONS,
    build_system_prompt,
    build_user_prompt,
    validate_and_normalize_questions,
)

logger = logging.getLogger(__name__)

MODEL_FALLBACKS = (
    'step-3.7-flash',
    'step-3.5-flash',
    'step-3.5-flash-2603',
)

MAX_RETRIES_PER_MODEL = 2
RETRY_DELAYS_SEC = (1.5, 3.0)


class StepfunHTTPError(Exception):
    def __init__(self, code: int, message: str, raw: str = ''):
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(message)


def stepfun_configured() -> bool:
    return bool(settings.STEPFUN_API_KEY)


def _parse_api_error(detail: str) -> str:
    try:
        data = json.loads(detail)
        message = data.get('error', {}).get('message', '')
        if message:
            return message
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass
    return detail.strip()[:400] or '未知错误'


def _is_auth_error(code: int, message: str) -> bool:
    if code in (401, 403):
        return True
    lowered = message.lower()
    return 'api key' in lowered or 'unauthorized' in lowered or 'permission' in lowered


def _is_model_not_found(code: int, message: str) -> bool:
    if code == 404:
        return True
    lowered = message.lower()
    return 'model' in lowered and ('not found' in lowered or 'does not exist' in lowered)


def _is_transient_capacity_error(code: int, message: str) -> bool:
    if code in (503, 429, 500, 502):
        return True
    lowered = message.lower()
    return (
        'high demand' in lowered
        or 'resource exhausted' in lowered
        or 'overloaded' in lowered
        or 'try again later' in lowered
        or 'rate limit' in lowered
    )


def _chat_completions_url() -> str:
    base = settings.STEPFUN_BASE_URL.rstrip('/')
    return f'{base}/chat/completions'


def _request_chat(body: dict) -> dict:
    api_key = settings.STEPFUN_API_KEY
    req = urllib.request.Request(
        _chat_completions_url(),
        data=json.dumps(body).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', errors='replace')
        message = _parse_api_error(detail)
        logger.warning('StepFun HTTP %s: %s', e.code, message[:300])
        raise StepfunHTTPError(e.code, message, detail) from e
    except urllib.error.URLError as e:
        logger.warning('StepFun network error: %s', e)
        raise AIShootError('无法连接阶跃星辰 API，请检查网络后重试。') from e


def _models_to_try() -> list[str]:
    configured = (settings.STEPFUN_MODEL or '').strip()
    ordered: list[str] = []

    def add(model_id: str) -> None:
        if model_id and model_id not in ordered:
            ordered.append(model_id)

    if configured:
        add(configured)
    for model_id in MODEL_FALLBACKS:
        add(model_id)

    return ordered


def _build_chat_body(model: str, topic: str, description: str, counts: dict[str, int]) -> dict:
    return {
        'model': model,
        'messages': [
            {'role': 'system', 'content': build_system_prompt()},
            {'role': 'user', 'content': build_user_prompt(topic, description, counts)},
        ],
        'response_format': {'type': 'json_object'},
        'temperature': 0.7,
    }


def _raise_final_error(tried_models: list[str], last: StepfunHTTPError | None) -> None:
    if last:
        message = last.message
        code = last.code
    else:
        message = '所有模型均不可用'
        code = 0

    tried = '、'.join(tried_models[:6]) if tried_models else '无'
    hint = ''
    if _is_auth_error(code, message):
        hint = (
            ' 请在阶跃星辰开放平台创建 API Key 并设置环境变量 STEPFUN_API_KEY。'
            '文档：https://platform.stepfun.com/docs/zh/quickstart/overview'
        )
    elif _is_model_not_found(code, message):
        hint = f' 已尝试模型：{tried}。可设置 STEPFUN_MODEL=step-3.7-flash。'
    elif _is_transient_capacity_error(code, message):
        hint = ' 服务繁忙，请稍后再试或减少题目数量。'

    raise AIShootError(f'AI 服务请求失败 ({code})：{message}.{hint}')


def _parse_chat_response(payload: dict) -> list:
    try:
        choice = payload['choices'][0]
        finish_reason = choice.get('finish_reason', '')
        if finish_reason == 'length':
            raise AIShootError('AI 输出被长度限制截断，请减少题目数量后重试。')
        content = choice['message']['content']
        data = json.loads(content)
        return data['questions']
    except (KeyError, IndexError, json.JSONDecodeError, TypeError) as e:
        logger.warning('StepFun parse error: %s', str(payload)[:500])
        raise AIShootError('AI 返回格式异常，请重试。') from e


def generate_shoot_questions(
    topic: str,
    description: str,
    counts: dict[str, int],
) -> list[dict]:
    if not stepfun_configured():
        raise AIShootError(
            '未配置 STEPFUN_API_KEY。请在阶跃星辰开放平台获取 API Key 后设置环境变量。'
        )

    total = sum(counts.values())
    if total == 0:
        raise AIShootError('请至少指定 1 道题')
    if total > MAX_TOTAL_QUESTIONS:
        raise AIShootError(f'题目总数不能超过 {MAX_TOTAL_QUESTIONS} 道')

    models = _models_to_try()
    tried: list[str] = []
    last_error: StepfunHTTPError | None = None
    raw_questions = None
    used_model = None

    for model in models:
        if model in tried:
            continue
        tried.append(model)
        body = _build_chat_body(model, topic, description, counts)

        for attempt in range(MAX_RETRIES_PER_MODEL + 1):
            try:
                payload = _request_chat(body)
                raw_questions = _parse_chat_response(payload)
                used_model = model
                break
            except StepfunHTTPError as e:
                last_error = e
                if _is_model_not_found(e.code, e.message):
                    logger.info('StepFun model %s not available, trying next', model)
                    break
                if _is_transient_capacity_error(e.code, e.message):
                    if attempt < MAX_RETRIES_PER_MODEL:
                        delay = RETRY_DELAYS_SEC[attempt]
                        logger.info(
                            'StepFun model %s busy (%s), retry in %.1fs',
                            model, e.code, delay,
                        )
                        time.sleep(delay)
                        continue
                    logger.info(
                        'StepFun model %s still busy, trying next model', model,
                    )
                    break
                _raise_final_error(tried, e)
            except AIShootError:
                raise

        if raw_questions is not None:
            break

    if raw_questions is None:
        _raise_final_error(tried, last_error)

    logger.info('StepFun generation succeeded with model %s', used_model)
    return validate_and_normalize_questions(raw_questions, counts)
