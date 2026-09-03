from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_player_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='show_question_stem',
            field=models.BooleanField(
                default=True,
                help_text='关闭后学生端只显示铺满屏幕的选项或输入框，题干由公共屏幕展示。',
                verbose_name='学生端显示题干和图片',
            ),
        ),
    ]
