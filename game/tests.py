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


class AvatarFeatureTests(TestCase):
    def test_player_avatar_parsing(self):
        from .models import Player, Room
        room = Room.objects.create(code='123456', name='Test Room')
        p = Player.objects.create(
            room=room,
            nickname='Alex',
            session_id='sess_1',
            avatar='{"face": 2, "hair": 4}',
        )
        self.assertEqual(p.get_avatar_dict(), {'face': 2, 'hair': 4})

        # Test malformed avatar fallback
        p_bad = Player.objects.create(
            room=room,
            nickname='Bob',
            session_id='sess_2',
            avatar='invalid json',
        )
        self.assertEqual(p_bad.get_avatar_dict(), {'face': 0, 'hair': 0})

    def test_room_cache_avatar_update(self):
        from .models import Room
        from .room_cache import get_runtime, join_player, update_player_avatar
        room = Room.objects.create(code='888999', name='Cache Room')
        runtime = get_runtime(room)

        # Join with avatar
        cached, created, err = join_player(
            runtime, 'Charlie', 'sess_3', avatar={'face': 1, 'hair': 3},
        )
        self.assertIsNone(err)
        self.assertEqual(cached.avatar, {'face': 1, 'hair': 3})

        # Update avatar
        updated, ok = update_player_avatar(runtime, 'sess_3', {'face': 5, 'hair': 2})
        self.assertTrue(ok)
        self.assertEqual(updated.avatar, {'face': 5, 'hair': 2})

        # Check leaderboard includes avatar
        lb = runtime.get_leaderboard()
        self.assertEqual(len(lb), 1)
        self.assertEqual(lb[0]['avatar'], {'face': 5, 'hair': 2})

