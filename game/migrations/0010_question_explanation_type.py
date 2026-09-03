from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0009_room_show_question_stem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.CharField(
                choices=[
                    ('single', '单选题'),
                    ('multiple', '多选题'),
                    ('judgment', '判断题'),
                    ('short_answer', '简答题'),
                    ('word_cloud', '词云题'),
                    ('explanation', '解释'),
                ],
                default='single',
                max_length=20,
                verbose_name='题型',
            ),
        ),
    ]
