"""Text normalization for short-answer and word-cloud questions."""

SHORT_ANSWER_MAX_LENGTH = 100
WORD_CLOUD_MAX_LENGTH = 40


def normalize_answer_text(text: str) -> str:
    return ' '.join(text.strip().split()).lower()


def normalize_word_cloud_text(text: str) -> str:
    cleaned = ' '.join(text.strip().split())
    return cleaned[:WORD_CLOUD_MAX_LENGTH]


def split_acceptable_answers(raw: str) -> list[str]:
    if not raw:
        return []
    parts = raw.replace('\n', '|').split('|')
    return [p.strip() for p in parts if p.strip()]
