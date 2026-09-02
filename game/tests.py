from django.test import TestCase

from .models import Question


class MultipleChoiceScoringTests(TestCase):
    def _make_multiple(self, correct_option: str) -> Question:
        return Question(
            text='test',
            question_type=Question.TYPE_MULTIPLE,
            option_a='A',
            option_b='B',
            option_c='C',
            option_d='D',
            correct_option=correct_option,
        )

    def test_exact_match_scores(self):
        q = self._make_multiple('A,C')
        self.assertTrue(q.is_multiple_choice_correct('A,C'))
        self.assertTrue(q.is_multiple_choice_correct('C,A'))

    def test_partial_selection_no_score(self):
        q = self._make_multiple('A,C')
        self.assertFalse(q.is_multiple_choice_correct('A'))
        self.assertFalse(q.is_multiple_choice_correct('C'))

    def test_extra_wrong_option_no_score(self):
        q = self._make_multiple('A,C')
        self.assertFalse(q.is_multiple_choice_correct('A,B,C'))
        self.assertFalse(q.is_multiple_choice_correct('A,B'))

    def test_wrong_only_no_score(self):
        q = self._make_multiple('A,C')
        self.assertFalse(q.is_multiple_choice_correct('B,D'))

    def test_correct_without_comma_still_parsed(self):
        q = self._make_multiple('AC')
        self.assertTrue(q.is_multiple_choice_correct('A,C'))
        self.assertFalse(q.is_multiple_choice_correct('A'))
