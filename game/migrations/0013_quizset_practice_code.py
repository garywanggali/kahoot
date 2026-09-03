from django.db import migrations, models
from django.db.models import Q


def assign_practice_codes(apps, schema_editor):
    QuizSet = apps.get_model('game', 'QuizSet')
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    existing = set(
        QuizSet.objects.exclude(practice_code__isnull=True)
        .exclude(practice_code='')
        .values_list('practice_code', flat=True)
    )

    def next_code():
        import random
        while True:
            code = ''.join(random.choices(alphabet, k=6))
            if code not in existing:
                existing.add(code)
                return code

    for quiz_set in QuizSet.objects.filter(is_public=True).filter(
        Q(practice_code__isnull=True) | Q(practice_code=''),
    ):
        quiz_set.practice_code = next_code()
        quiz_set.save(update_fields=['practice_code'])


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0012_room_reveal_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizset',
            name='practice_code',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='公开套题的 6 位字母练习码，学生在首页输入后进入个人练习。',
                max_length=6,
                null=True,
                unique=True,
                verbose_name='练习码',
            ),
        ),
        migrations.CreateModel(
            name='PracticeAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nickname', models.CharField(max_length=50, verbose_name='昵称')),
                ('token', models.CharField(db_index=True, max_length=64, unique=True)),
                ('avatar', models.CharField(default='{"face":0,"hair":0}', max_length=120, verbose_name='个性化头像')),
                ('score', models.IntegerField(default=0)),
                ('answers', models.JSONField(default=list)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('quiz_set', models.ForeignKey(
                    on_delete=models.CASCADE,
                    related_name='practice_attempts',
                    to='game.quizset',
                )),
            ],
            options={
                'ordering': ['-score', 'finished_at', 'started_at'],
            },
        ),
        migrations.AddIndex(
            model_name='practiceattempt',
            index=models.Index(fields=['quiz_set', 'score'], name='game_practice_quiz_score_idx'),
        ),
        migrations.RunPython(assign_practice_codes, migrations.RunPython.noop),
    ]
