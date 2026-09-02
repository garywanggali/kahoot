import random
import string

from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from .text_utils import normalize_answer_text, split_acceptable_answers
from .validators import validate_question_image


class Teacher(models.Model):
    username = models.CharField('用户名', max_length=50, unique=True, db_index=True)
    password_hash = models.CharField(max_length=128)
    display_name = models.CharField('显示名', max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.username

    def set_password(self, raw_password: str) -> None:
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password_hash)


class TeacherInviteCode(models.Model):
    code = models.CharField('邀请码', max_length=32, unique=True, db_index=True)
    max_uses = models.PositiveIntegerField('可用次数', default=1)
    used_count = models.PositiveIntegerField('已使用次数', default=0)
    is_active = models.BooleanField('启用', default=True)
    note = models.CharField('备注', max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def can_use(self) -> bool:
        return self.is_active and self.used_count < self.max_uses

    def consume(self) -> None:
        self.used_count += 1
        self.save(update_fields=['used_count'])


class Question(models.Model):
    OPTION_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]
    TYPE_SINGLE = 'single'
    TYPE_MULTIPLE = 'multiple'
    TYPE_JUDGMENT = 'judgment'
    TYPE_SHORT_ANSWER = 'short_answer'
    TYPE_WORD_CLOUD = 'word_cloud'
    TYPE_CHOICES = [
        (TYPE_SINGLE, '单选题'),
        (TYPE_MULTIPLE, '多选题'),
        (TYPE_JUDGMENT, '判断题'),
        (TYPE_SHORT_ANSWER, '简答题'),
        (TYPE_WORD_CLOUD, '词云题'),
    ]
    JUDGMENT_OPTION_PLACEHOLDER = '—'
    TEXT_OPTION_PLACEHOLDER = '—'

    text = models.CharField('题目', max_length=500)
    question_type = models.CharField(
        '题型', max_length=20, choices=TYPE_CHOICES, default=TYPE_SINGLE,
    )
    image = models.ImageField(
        '题目图片',
        upload_to='questions/',
        blank=True,
        null=True,
        validators=[validate_question_image],
    )
    option_a = models.CharField('选项 A', max_length=200)
    option_b = models.CharField('选项 B', max_length=200)
    option_c = models.CharField('选项 C', max_length=200)
    option_d = models.CharField('选项 D', max_length=200)
    correct_option = models.CharField('正确答案', max_length=10)
    time_limit = models.PositiveIntegerField('答题时限(秒)', default=20)
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='questions',
        null=True,
        blank=True,
    )
    is_public = models.BooleanField('公开题库', default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.text[:50]

    def get_options(self):
        if self.question_type == self.TYPE_JUDGMENT:
            return [
                {'key': 'A', 'text': self.option_a},
                {'key': 'B', 'text': self.option_b},
            ]
        if self.question_type in (self.TYPE_SHORT_ANSWER, self.TYPE_WORD_CLOUD):
            return []
        return [
            {'key': 'A', 'text': self.option_a},
            {'key': 'B', 'text': self.option_b},
            {'key': 'C', 'text': self.option_c},
            {'key': 'D', 'text': self.option_d},
        ]

    def get_correct_option_set(self):
        return {opt.strip().upper() for opt in self.correct_option.split(',') if opt.strip()}

    def get_correct_option_display(self):
        if self.question_type == self.TYPE_SHORT_ANSWER:
            return self.option_a.replace('|', ' / ')
        if self.question_type == self.TYPE_WORD_CLOUD:
            return '词云统计'
        if self.question_type == self.TYPE_JUDGMENT:
            key = self.correct_option.strip().upper()
            if key == 'A':
                return self.option_a
            if key == 'B':
                return self.option_b
        return ', '.join(sorted(self.get_correct_option_set()))

    @property
    def correct_option_keys(self):
        return sorted(self.get_correct_option_set())

    def is_answer_correct(self, selected):
        if self.question_type == self.TYPE_SHORT_ANSWER:
            return self.is_text_answer_correct(selected)
        if self.question_type == self.TYPE_WORD_CLOUD:
            return bool(selected and selected.strip())
        selected_set = {opt.strip().upper() for opt in selected.split(',') if opt.strip()}
        return selected_set == self.get_correct_option_set()

    def is_text_answer_correct(self, text: str) -> bool:
        normalized = normalize_answer_text(text)
        if not normalized:
            return False
        acceptable = {normalize_answer_text(a) for a in split_acceptable_answers(self.option_a)}
        return normalized in acceptable


class Room(models.Model):
    STATUS_WAITING = 'waiting'
    STATUS_PLAYING = 'playing'
    STATUS_LEADERBOARD = 'leaderboard'
    STATUS_ENDED = 'ended'

    STATUS_CHOICES = [
        (STATUS_WAITING, '等待中'),
        (STATUS_PLAYING, '答题中'),
        (STATUS_LEADERBOARD, '排行榜'),
        (STATUS_ENDED, '已结束'),
    ]

    code = models.CharField('房间号', max_length=6, unique=True, db_index=True)
    name = models.CharField('房间名称', max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WAITING)
    current_question_index = models.IntegerField(default=-1)
    question_started_at = models.DateTimeField(null=True, blank=True)
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='rooms',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} - {self.name or "未命名"}'

    @staticmethod
    def generate_code():
        chars = string.digits
        while True:
            code = ''.join(random.choices(chars, k=6))
            if not Room.objects.filter(code=code).exists():
                return code

    def get_questions(self):
        return [rq.question for rq in self.room_questions.select_related('question').order_by('order')]

    def current_question(self):
        questions = self.get_questions()
        if 0 <= self.current_question_index < len(questions):
            return questions[self.current_question_index]
        return None


class RoomQuestion(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ['room', 'question']


class Player(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    nickname = models.CharField('昵称', max_length=50)
    score = models.IntegerField(default=0)
    session_id = models.CharField(max_length=64, db_index=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['room', 'nickname']

    def __str__(self):
        return f'{self.nickname} ({self.score})'


class Answer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='answers')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    points = models.IntegerField(default=0)
    response_time_ms = models.IntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['player', 'question']
