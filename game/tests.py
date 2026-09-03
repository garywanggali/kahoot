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


class AnalyticsFeatureTests(TestCase):
    def setUp(self):
        from .models import Answer, Player, Question, Room, RoomQuestion, Teacher
        self.teacher = Teacher.objects.create(username='t_analyst')
        self.teacher.set_password('password123')
        self.teacher.save()
        self.room = Room.objects.create(code='654321', name='Analytics Room', teacher=self.teacher)

        self.q1 = Question.objects.create(
            text='中国的首都是？',
            question_type=Question.TYPE_SINGLE,
            option_a='北京',
            option_b='上海',
            option_c='广州',
            option_d='深圳',
            correct_option='A',
            time_limit=20,
        )
        self.q2 = Question.objects.create(
            text='地球是平的？',
            question_type=Question.TYPE_JUDGMENT,
            option_a='正确',
            option_b='错误',
            correct_option='B',
            time_limit=15,
        )
        RoomQuestion.objects.create(room=self.room, question=self.q1, order=1)
        RoomQuestion.objects.create(room=self.room, question=self.q2, order=2)

        self.p1 = Player.objects.create(room=self.room, nickname='Alice', session_id='s1', score=1800)
        self.p2 = Player.objects.create(room=self.room, nickname='Bob', session_id='s2', score=900)
        self.p3 = Player.objects.create(room=self.room, nickname='Cindy', session_id='s3', score=0)

        # Alice: Q1 right, Q2 right
        Answer.objects.create(room=self.room, player=self.p1, question=self.q1, selected_option='A', is_correct=True, points=950, response_time_ms=1200)
        Answer.objects.create(room=self.room, player=self.p1, question=self.q2, selected_option='B', is_correct=True, points=850, response_time_ms=2100)

        # Bob: Q1 right, Q2 wrong
        Answer.objects.create(room=self.room, player=self.p2, question=self.q1, selected_option='A', is_correct=True, points=900, response_time_ms=1500)
        Answer.objects.create(room=self.room, player=self.p2, question=self.q2, selected_option='A', is_correct=False, points=0, response_time_ms=3000)

        # Cindy: Q1 wrong, Q2 unanswered
        Answer.objects.create(room=self.room, player=self.p3, question=self.q1, selected_option='B', is_correct=False, points=0, response_time_ms=4500)

    def test_get_room_analytics_data(self):
        from .analytics import get_room_analytics_data
        data = get_room_analytics_data(self.room)

        # 1. Summary
        summary = data['summary']
        self.assertEqual(summary['total_players'], 3)
        self.assertEqual(summary['total_questions'], 2)
        self.assertEqual(summary['highest_score'], 1800)
        # 3 correct out of 6 possible answers => 50.0%
        self.assertEqual(summary['overall_accuracy'], 50.0)

        # 2. By Question
        by_q = data['by_questions']
        self.assertEqual(len(by_q), 2)

        # Q1: 2 correct (Alice, Bob), 1 wrong (Cindy)
        q1_data = by_q[0]
        self.assertEqual(q1_data['id'], self.q1.id)
        self.assertEqual(q1_data['correct_count'], 2)
        self.assertEqual(q1_data['wrong_count'], 1)
        self.assertEqual(q1_data['unanswered_count'], 0)
        self.assertEqual([p['nickname'] for p in q1_data['correct_players']], ['Alice', 'Bob'])
        self.assertEqual([p['nickname'] for p in q1_data['wrong_players']], ['Cindy'])

        # Q2: 1 correct (Alice), 1 wrong (Bob), 1 unanswered (Cindy)
        q2_data = by_q[1]
        self.assertEqual(q2_data['id'], self.q2.id)
        self.assertEqual(q2_data['correct_count'], 1)
        self.assertEqual(q2_data['wrong_count'], 1)
        self.assertEqual(q2_data['unanswered_count'], 1)
        self.assertEqual([p['nickname'] for p in q2_data['correct_players']], ['Alice'])
        self.assertEqual([p['nickname'] for p in q2_data['wrong_players']], ['Bob'])
        self.assertEqual([p['nickname'] for p in q2_data['unanswered_players']], ['Cindy'])

        # 3. By Player
        by_p = data['by_players']
        self.assertEqual(len(by_p), 3)

        # Alice: 2 correct, 0 wrong
        p1_data = next(p for p in by_p if p['nickname'] == 'Alice')
        self.assertEqual(p1_data['correct_count'], 2)
        self.assertEqual(p1_data['wrong_count'], 0)
        self.assertEqual(p1_data['unanswered_count'], 0)
        self.assertEqual(len(p1_data['correct_questions']), 2)

        # Bob: 1 correct (Q1), 1 wrong (Q2)
        p2_data = next(p for p in by_p if p['nickname'] == 'Bob')
        self.assertEqual(p2_data['correct_count'], 1)
        self.assertEqual(p2_data['wrong_count'], 1)
        self.assertEqual(p2_data['correct_questions'][0]['order'], 1)
        self.assertEqual(p2_data['wrong_questions'][0]['order'], 2)

        # Cindy: 0 correct, 1 wrong (Q1), 1 unanswered (Q2)
        p3_data = next(p for p in by_p if p['nickname'] == 'Cindy')
        self.assertEqual(p3_data['correct_count'], 0)
        self.assertEqual(p3_data['wrong_count'], 1)
        self.assertEqual(p3_data['unanswered_count'], 1)
        self.assertEqual(p3_data['wrong_questions'][0]['order'], 1)
        self.assertEqual(p3_data['unanswered_questions'][0]['order'], 2)

    def test_analytics_views(self):
        from django.urls import reverse
        session = self.client.session
        session['teacher_id'] = self.teacher.pk
        session.save()

        # API
        api_url = reverse('room_analytics_data', kwargs={'pk': self.room.pk})
        resp = self.client.get(api_url)
        self.assertEqual(resp.status_code, 200)
        json_data = resp.json()
        self.assertIn('by_questions', json_data)
        self.assertIn('by_players', json_data)

        # Page
        page_url = reverse('room_analytics_page', kwargs={'pk': self.room.pk})
        resp_page = self.client.get(page_url)
        self.assertEqual(resp_page.status_code, 200)
        self.assertContains(resp_page, '对战数据分析报告')


class JoinRoomViewTests(TestCase):
    def test_invalid_room_code_preserves_landing_ui(self):
        from django.urls import reverse
        resp = self.client.post(reverse('join_room'), {
            'code': '999999',
            'nickname': 'TestUser',
        })
        self.assertEqual(resp.status_code, 422)
        content = resp.content.decode('utf-8')
        # Check that signature headline is preserved
        self.assertIn('every question.', content)
        self.assertIn('every answer.', content)
        # Check that 3D floating keycaps stage is preserved
        self.assertIn('keycaps-stage', content)
        # Check that unwanted text badges are absent
        self.assertNotIn('PLAYER_LOGIN // v2.0', content)
        self.assertNotIn('join game.', content)
        # Check that error message is displayed
        self.assertIn('房间号不存在', content)
        self.assertIn('join-inline-error', content)

    def test_turbo_script_served_locally(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        self.assertIn('turbo.min.js', content)
        self.assertNotIn('https://cdn.jsdelivr.net/npm/@hotwired/turbo@8.0.12/dist/turbo.min.js', content)



