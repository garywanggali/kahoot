# Generated manually for QuizSet bundle model

from django.db import migrations, models
import django.db.models.deletion


def backfill_quiz_sets(apps, schema_editor):
    Teacher = apps.get_model('game', 'Teacher')
    Question = apps.get_model('game', 'Question')
    QuizSet = apps.get_model('game', 'QuizSet')
    QuizSetQuestion = apps.get_model('game', 'QuizSetQuestion')

    for teacher in Teacher.objects.all():
        questions = list(
            Question.objects.filter(teacher_id=teacher.pk).order_by('created_at')
        )
        if not questions:
            continue
        quiz_set = QuizSet.objects.create(
            title='未归类题目',
            teacher_id=teacher.pk,
            is_public=False,
        )
        for order, question in enumerate(questions):
            QuizSetQuestion.objects.create(
                quiz_set_id=quiz_set.pk,
                question_id=question.pk,
                order=order,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0006_teacher_teacherinvitecode_question_is_public_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuizSet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='名称')),
                ('is_public', models.BooleanField(db_index=True, default=False, verbose_name='公开套题')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('teacher', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='quiz_sets',
                    to='game.teacher',
                )),
            ],
            options={
                'verbose_name': 'Shoot 套题',
                'verbose_name_plural': 'Shoot 套题',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='QuizSetQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(default=0)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.question')),
                ('quiz_set', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='quiz_set_questions',
                    to='game.quizset',
                )),
            ],
            options={
                'ordering': ['order'],
                'unique_together': {('quiz_set', 'question')},
            },
        ),
        migrations.AddField(
            model_name='room',
            name='source_quiz_set',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='rooms',
                to='game.quizset',
            ),
        ),
        migrations.RunPython(backfill_quiz_sets, migrations.RunPython.noop),
    ]
