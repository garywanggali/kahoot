from django.test import TestCase

from .excel_import import (
    ExcelImportError,
    build_template_xlsx,
    import_quiz_set_from_xlsx,
    read_rows_from_xlsx,
    validate_question_row,
)
from .models import Question, QuizSet, Teacher


class ExcelImportTests(TestCase):
    def setUp(self):
        self.teacher = Teacher.objects.create(username='t1')
        self.teacher.set_password('pass123')
        self.teacher.save()

    def test_template_and_import(self):
        xlsx = build_template_xlsx()
        quiz_set = import_quiz_set_from_xlsx(self.teacher, 'Excel 测试', xlsx)
        self.assertEqual(quiz_set.title, 'Excel 测试')
        self.assertEqual(quiz_set.question_count(), 4)
        types = [q.question_type for q in quiz_set.get_questions()]
        self.assertIn(Question.TYPE_MULTIPLE, types)

    def test_multiple_requires_two_correct(self):
        xlsx = build_template_xlsx()
        rows = read_rows_from_xlsx(xlsx)
        bad = dict(rows[1])
        bad['correct_option'] = 'A'
        bad.pop('excel_row')
        with self.assertRaises(ExcelImportError):
            validate_question_row(3, bad)

    def test_wrong_header_rejected(self):
        xlsx = build_template_xlsx()
        broken = b'not excel'
        with self.assertRaises(ExcelImportError):
            read_rows_from_xlsx(broken)

    def test_import_creates_quiz_set_only(self):
        before_q = Question.objects.count()
        before_s = QuizSet.objects.count()
        import_quiz_set_from_xlsx(self.teacher, '套题', build_template_xlsx())
        self.assertEqual(QuizSet.objects.count(), before_s + 1)
        self.assertEqual(Question.objects.count(), before_q + 4)
