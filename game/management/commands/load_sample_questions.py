from django.core.management.base import BaseCommand

from game.models import Question


class Command(BaseCommand):
    help = '导入示例单选题和多选题'

    def handle(self, *args, **options):
        samples = [
            {
                'text': '中国的首都是哪里？',
                'question_type': Question.TYPE_SINGLE,
                'option_a': '上海',
                'option_b': '北京',
                'option_c': '广州',
                'option_d': '深圳',
                'correct_option': 'B',
                'time_limit': 20,
            },
            {
                'text': '1 + 1 = ?',
                'question_type': Question.TYPE_SINGLE,
                'option_a': '1',
                'option_b': '2',
                'option_c': '3',
                'option_d': '4',
                'correct_option': 'B',
                'time_limit': 15,
            },
            {
                'text': 'Python 是一种什么类型的语言？',
                'question_type': Question.TYPE_SINGLE,
                'option_a': '编译型',
                'option_b': '解释型',
                'option_c': '汇编语言',
                'option_d': '机器语言',
                'correct_option': 'B',
                'time_limit': 20,
            },
            {
                'text': '地球围绕什么旋转？',
                'question_type': Question.TYPE_SINGLE,
                'option_a': '月球',
                'option_b': '太阳',
                'option_c': '火星',
                'option_d': '木星',
                'correct_option': 'B',
                'time_limit': 20,
            },
            {
                'text': '一年有多少个月？',
                'question_type': Question.TYPE_SINGLE,
                'option_a': '10',
                'option_b': '11',
                'option_c': '12',
                'option_d': '13',
                'correct_option': 'C',
                'time_limit': 15,
            },
            {
                'text': '下列哪些属于编程语言？（多选）',
                'question_type': Question.TYPE_MULTIPLE,
                'option_a': 'Python',
                'option_b': 'HTML',
                'option_c': 'Java',
                'option_d': 'JPEG',
                'correct_option': 'A,C',
                'time_limit': 25,
            },
            {
                'text': '下列哪些是偶数？（多选）',
                'question_type': Question.TYPE_MULTIPLE,
                'option_a': '2',
                'option_b': '3',
                'option_c': '4',
                'option_d': '7',
                'correct_option': 'A,C',
                'time_limit': 20,
            },
            {
                'text': '下列哪些是中国四大名著？（多选）',
                'question_type': Question.TYPE_MULTIPLE,
                'option_a': '红楼梦',
                'option_b': '西游记',
                'option_c': '水浒传',
                'option_d': '聊斋志异',
                'correct_option': 'A,B,C',
                'time_limit': 30,
            },
            {
                'text': '下列哪些是可再生能源？（多选）',
                'question_type': Question.TYPE_MULTIPLE,
                'option_a': '太阳能',
                'option_b': '煤炭',
                'option_c': '风能',
                'option_d': '石油',
                'correct_option': 'A,C',
                'time_limit': 25,
            },
            {
                'text': '下列哪些动物是哺乳动物？（多选）',
                'question_type': Question.TYPE_MULTIPLE,
                'option_a': '海豚',
                'option_b': '企鹅',
                'option_c': '蝙蝠',
                'option_d': '鳄鱼',
                'correct_option': 'A,C',
                'time_limit': 25,
            },
            {
                'text': '地球是圆的。',
                'question_type': Question.TYPE_JUDGMENT,
                'option_a': '正确',
                'option_b': '错误',
                'option_c': Question.JUDGMENT_OPTION_PLACEHOLDER,
                'option_d': Question.JUDGMENT_OPTION_PLACEHOLDER,
                'correct_option': 'A',
                'time_limit': 15,
            },
            {
                'text': '太阳从西边升起。',
                'question_type': Question.TYPE_JUDGMENT,
                'option_a': '正确',
                'option_b': '错误',
                'option_c': Question.JUDGMENT_OPTION_PLACEHOLDER,
                'option_d': Question.JUDGMENT_OPTION_PLACEHOLDER,
                'correct_option': 'B',
                'time_limit': 15,
            },
        ]

        created = 0
        for data in samples:
            _, was_created = Question.objects.get_or_create(
                text=data['text'],
                defaults=data,
            )
            if was_created:
                created += 1

        single_count = Question.objects.filter(question_type=Question.TYPE_SINGLE).count()
        multiple_count = Question.objects.filter(question_type=Question.TYPE_MULTIPLE).count()
        judgment_count = Question.objects.filter(question_type=Question.TYPE_JUDGMENT).count()
        self.stdout.write(self.style.SUCCESS(
            f'已导入 {created} 道新题目，题库共 {Question.objects.count()} 道'
            f'（单选 {single_count}，多选 {multiple_count}，判断 {judgment_count}）'
        ))
