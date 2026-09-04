from django.core.management.base import BaseCommand

from game.models import Question, QuizSet, Teacher
from game.practice_utils import ensure_practice_code
from game.quiz_set_utils import add_question_to_quiz_set

MARKET_USERNAME = 'kahoot_market'
MARKET_DISPLAY_NAME = '题库精选'


def _q(text, qtype, option_a, option_b, option_c, option_d, correct, time_limit=20):
    return {
        'text': text,
        'question_type': qtype,
        'option_a': option_a,
        'option_b': option_b,
        'option_c': option_c,
        'option_d': option_d,
        'correct_option': correct,
        'time_limit': time_limit,
    }


def _wc(text, time_limit=30):
    dash = Question.TEXT_OPTION_PLACEHOLDER
    return _q(text, Question.TYPE_WORD_CLOUD, dash, dash, dash, dash, '', time_limit)


PUBLIC_CATALOG = [
    {
        'title': '世界地理入门',
        'questions': [
            _q('中国的首都是哪里？', Question.TYPE_SINGLE, '上海', '北京', '广州', '深圳', 'B'),
            _q('世界上面积最大的国家是？', Question.TYPE_SINGLE, '中国', '加拿大', '俄罗斯', '美国', 'C'),
            _q('尼罗河流经哪一大洲？', Question.TYPE_SINGLE, '亚洲', '非洲', '欧洲', '南美洲', 'B'),
            _q('下列哪些是岛国？（多选）', Question.TYPE_MULTIPLE, '日本', '蒙古', '英国', '瑞士', 'A,C', 25),
            _q('赤道穿过非洲。', Question.TYPE_JUDGMENT, '正确', '错误', Question.JUDGMENT_OPTION_PLACEHOLDER, Question.JUDGMENT_OPTION_PLACEHOLDER, 'A', 15),
        ],
    },
    {
        'title': '小学数学口算',
        'questions': [
            _q('7 × 8 = ?', Question.TYPE_SINGLE, '54', '56', '63', '64', 'B', 15),
            _q('100 − 37 = ?', Question.TYPE_SINGLE, '63', '67', '73', '77', 'A', 15),
            _q('12 ÷ 4 = ?', Question.TYPE_SINGLE, '2', '3', '4', '6', 'B', 12),
            _q('下列哪些是偶数？（多选）', Question.TYPE_MULTIPLE, '2', '3', '8', '9', 'A,C', 20),
            _q('直角是 90 度。', Question.TYPE_JUDGMENT, '正确', '错误', Question.JUDGMENT_OPTION_PLACEHOLDER, Question.JUDGMENT_OPTION_PLACEHOLDER, 'A', 12),
        ],
    },
    {
        'title': '中国历史常识',
        'questions': [
            _q('秦始皇统一六国后建立的朝代是？', Question.TYPE_SINGLE, '汉朝', '秦朝', '唐朝', '宋朝', 'B'),
            _q('《史记》的作者是？', Question.TYPE_SINGLE, '司马光', '司马迁', '班固', '孔子', 'B'),
            _q('下列哪些是中国四大名著？（多选）', Question.TYPE_MULTIPLE, '红楼梦', '西游记', '水浒传', '聊斋志异', 'A,B,C', 30),
            _q('丝绸之路在汉代开通。', Question.TYPE_JUDGMENT, '正确', '错误', Question.JUDGMENT_OPTION_PLACEHOLDER, Question.JUDGMENT_OPTION_PLACEHOLDER, 'A', 15),
            _q('唐朝的都城是哪里？（简答）', Question.TYPE_SHORT_ANSWER, '长安|西安', Question.TEXT_OPTION_PLACEHOLDER, Question.TEXT_OPTION_PLACEHOLDER, Question.TEXT_OPTION_PLACEHOLDER, 'A', 25),
        ],
    },
    {
        'title': '科学判断小测验',
        'questions': [
            _q('地球围绕太阳公转。', Question.TYPE_JUDGMENT, '正确', '错误', Question.JUDGMENT_OPTION_PLACEHOLDER, Question.JUDGMENT_OPTION_PLACEHOLDER, 'A', 12),
            _q('植物光合作用会释放氧气。', Question.TYPE_JUDGMENT, '正确', '错误', Question.JUDGMENT_OPTION_PLACEHOLDER, Question.JUDGMENT_OPTION_PLACEHOLDER, 'A', 12),
            _q('声音在真空中传播得更快。', Question.TYPE_JUDGMENT, '正确', '错误', Question.JUDGMENT_OPTION_PLACEHOLDER, Question.JUDGMENT_OPTION_PLACEHOLDER, 'B', 15),
            _q('下列哪些是可再生能源？（多选）', Question.TYPE_MULTIPLE, '太阳能', '煤炭', '风能', '石油', 'A,C', 25),
            _q('水的化学分子式是？（简答）', Question.TYPE_SHORT_ANSWER, 'H2O|H₂O', Question.TEXT_OPTION_PLACEHOLDER, Question.TEXT_OPTION_PLACEHOLDER, Question.TEXT_OPTION_PLACEHOLDER, 'A', 20),
        ],
    },
    {
        'title': '趣味英语词汇',
        'questions': [
            _q('Apple 的中文意思是？', Question.TYPE_SINGLE, '香蕉', '苹果', '橙子', '葡萄', 'B', 12),
            _q('Which word means “快乐”？', Question.TYPE_SINGLE, 'sad', 'angry', 'happy', 'tired', 'C', 15),
            _q('Dog 是哪种动物？', Question.TYPE_SINGLE, '猫', '狗', '鸟', '鱼', 'B', 12),
            _q('下列哪些是颜色单词？（多选）', Question.TYPE_MULTIPLE, 'red', 'run', 'blue', 'jump', 'A,C', 20),
            _q('“谢谢”用英语怎么说？（简答）', Question.TYPE_SHORT_ANSWER, 'thank you|thanks|Thank you|Thanks', Question.TEXT_OPTION_PLACEHOLDER, Question.TEXT_OPTION_PLACEHOLDER, Question.TEXT_OPTION_PLACEHOLDER, 'A', 20),
        ],
    },
    {
        'title': '课堂暖场词云',
        'questions': [
            _wc('用一个词形容今天的心情'),
            _wc('提到“中国”，你最先想到哪个词？'),
            _wc('这学期你最想学会什么？', 40),
        ],
    },
]


def seed_public_catalog():
    teacher, created_teacher = Teacher.objects.get_or_create(
        username=MARKET_USERNAME,
        defaults={'display_name': MARKET_DISPLAY_NAME, 'is_active': True},
    )
    if created_teacher or not teacher.password_hash:
        teacher.set_password('market-demo-not-for-login')
        teacher.display_name = MARKET_DISPLAY_NAME
        teacher.save()
    elif teacher.display_name != MARKET_DISPLAY_NAME:
        teacher.display_name = MARKET_DISPLAY_NAME
        teacher.save(update_fields=['display_name'])

    created_sets = 0
    created_questions = 0
    for item in PUBLIC_CATALOG:
        quiz_set, set_created = QuizSet.objects.get_or_create(
            teacher=teacher,
            title=item['title'],
            defaults={'is_public': True},
        )
        if not quiz_set.is_public:
            quiz_set.is_public = True
            quiz_set.save(update_fields=['is_public'])
        if set_created:
            created_sets += 1
        existing_texts = set(
            quiz_set.quiz_set_questions.select_related('question').values_list('question__text', flat=True)
        )
        for order, qdata in enumerate(item['questions']):
            if qdata['text'] in existing_texts:
                continue
            question = Question.objects.create(
                teacher=teacher,
                is_public=True,
                **qdata,
            )
            add_question_to_quiz_set(quiz_set, question, order=order)
            created_questions += 1
            existing_texts.add(qdata['text'])
        ensure_practice_code(quiz_set)

    return teacher, created_sets, created_questions


class Command(BaseCommand):
    help = '创建题库精选账号，并写入若干公开套题供公共题库浏览'

    def handle(self, *args, **options):
        teacher, created_sets, created_questions = seed_public_catalog()
        total = QuizSet.objects.filter(teacher=teacher, is_public=True).count()
        self.stdout.write(self.style.SUCCESS(
            f'公开题库已就绪：作者 {teacher.display_name}（{teacher.username}），'
            f'新增套题 {created_sets}，新增题目 {created_questions}，公开套题共 {total} 套'
        ))
