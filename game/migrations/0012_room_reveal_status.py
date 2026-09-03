from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0011_teacher_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='room',
            name='status',
            field=models.CharField(
                choices=[
                    ('waiting', '等待中'),
                    ('playing', '答题中'),
                    ('reveal', '揭晓统计'),
                    ('leaderboard', '排行榜'),
                    ('ended', '已结束'),
                ],
                default='waiting',
                max_length=20,
            ),
        ),
    ]
