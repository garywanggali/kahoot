from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0010_question_explanation_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='avatar',
            field=models.CharField(default='{"face":0,"hair":0}', max_length=120, verbose_name='个性化头像'),
        ),
        migrations.AddField(
            model_name='teacher',
            name='gender',
            field=models.CharField(
                choices=[
                    ('unspecified', '保密'),
                    ('female', '女'),
                    ('male', '男'),
                    ('other', '其他'),
                ],
                default='unspecified',
                max_length=16,
                verbose_name='性别',
            ),
        ),
    ]
