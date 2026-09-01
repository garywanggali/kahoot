from django.core.exceptions import ValidationError

MAX_QUESTION_IMAGE_BYTES = 2 * 1024 * 1024  # 2MB
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def validate_question_image(image):
    if image.size > MAX_QUESTION_IMAGE_BYTES:
        raise ValidationError(f'图片不能超过 {MAX_QUESTION_IMAGE_BYTES // (1024 * 1024)}MB')

    ext = '.' + image.name.rsplit('.', 1)[-1].lower() if '.' in image.name else ''
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError('仅支持 JPG、PNG、GIF、WEBP 格式')
