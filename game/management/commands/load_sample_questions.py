from django.core.management.base import BaseCommand

from game.models import Question


class Command(BaseCommand):
    help = '导入示例选择题'

    def handle(self, *args, **options):
        samples = [
            {
                'text': '中国的首都是哪里？',
                'option_a': '上海',
                'option_b': '北京',
                'option_c': '广州',
                'option_d': '深圳',
                'correct_option': 'B',
                'time_limit': 20,
            },
            {
                'text': '1 + 1 = ?',
                'option_a': '1',
                'option_b': '2',
                'option_c': '3',
                'option_d': '4',
                'correct_option': 'B',
                'time_limit': 15,
            },
            {
                'text': 'Python 是一种什么类型的语言？',
                'option_a': '编译型',
                'option_b': '解释型',
                'option_c': '汇编语言',
                'option_d': '机器语言',
                'correct_option': 'B',
                'time_limit': 20,
            },
            {
                'text': '地球围绕什么旋转？',
                'option_a': '月球',
                'option_b': '太阳',
                'option_c': '火星',
                'option_d': '木星',
                'correct_option': 'B',
                'time_limit': 20,
            },
            {
                'text': '一年有多少个月？',
                'option_a': '10',
                'option_b': '11',
                'option_c': '12',
                'option_d': '13',
                'correct_option': 'C',
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

        self.stdout.write(self.style.SUCCESS(f'已导入 {created} 道新题目，共 {Question.objects.count()} 道'))
