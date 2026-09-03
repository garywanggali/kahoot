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

    def test_flush_retries_after_player_already_persisted(self):
        from .models import Answer, Player, Question, Room
        from .room_cache import (
            drop_runtime,
            flush_runtime_force,
            get_runtime,
            join_player,
            record_answer,
        )

        room = Room.objects.create(code='777111', name='Flush Room')
        question = Question.objects.create(
            text='首都？',
            question_type=Question.TYPE_SINGLE,
            option_a='北京',
            option_b='上海',
            option_c='广州',
            option_d='深圳',
            correct_option='A',
        )
        runtime = get_runtime(room)
        cached, _created, err = join_player(runtime, 'Lee', 'sess-lee')
        self.assertIsNone(err)
        flush_runtime_force(runtime)
        self.assertIsNotNone(cached.db_id)
        self.assertEqual(Player.objects.filter(room=room).count(), 1)

        # Simulate a successful insert that never bound db_id back onto the cache.
        cached.db_id = None
        runtime.pending_players.append(cached)
        recorded = record_answer(
            runtime, 'sess-lee', question.id, 'A', True, 900, 1200,
        )
        self.assertTrue(recorded)
        flush_runtime_force(runtime)

        self.assertEqual(Player.objects.filter(room=room).count(), 1)
        self.assertEqual(Answer.objects.filter(room=room).count(), 1)
        answer = Answer.objects.get(room=room)
        self.assertTrue(answer.is_correct)
        self.assertEqual(answer.selected_option, 'A')
        drop_runtime(room.code)


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

    def test_room_created_success_does_not_show_on_landing(self):
        from django.contrib import messages
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.template.loader import render_to_string
        from django.test import RequestFactory

        request = RequestFactory().get('/')
        request.session = self.client.session
        setattr(request, '_messages', FallbackStorage(request))
        messages.success(request, '房间已创建，房间号: 020217')
        content = render_to_string(
            'game/index.html',
            {'messages': list(messages.get_messages(request))},
            request=request,
        )
        self.assertNotIn('房间已创建', content)
        self.assertNotIn('020217', content)


class QuestionRevealTests(TestCase):
    def _attach(self, room, question, order=0):
        from .models import RoomQuestion
        RoomQuestion.objects.create(room=room, question=question, order=order)

    def test_choice_question_counts_each_option_and_marks_correct(self):
        from .models import Player, Room
        from .utils import build_question_reveal

        room = Room.objects.create(code='111001', name='Reveal Room')
        question = Question.objects.create(
            text='首都？',
            question_type=Question.TYPE_SINGLE,
            option_a='北京',
            option_b='上海',
            option_c='广州',
            option_d='深圳',
            correct_option='A',
        )
        self._attach(room, question)
        Player.objects.create(room=room, nickname='A1', session_id='s1')
        Player.objects.create(room=room, nickname='A2', session_id='s2')
        Player.objects.create(room=room, nickname='A3', session_id='s3')
        from .models import Answer
        Answer.objects.create(
            room=room, player=Player.objects.get(session_id='s1'),
            question=question, selected_option='A', is_correct=True, points=800,
            response_time_ms=400,
        )
        Answer.objects.create(
            room=room, player=Player.objects.get(session_id='s2'),
            question=question, selected_option='B', is_correct=False, points=0,
            response_time_ms=500,
        )

        reveal = build_question_reveal(room, question)
        counts = {row['key']: row['count'] for row in reveal['option_stats']}
        self.assertEqual(counts, {'A': 1, 'B': 1, 'C': 0, 'D': 0})
        correct = [row['key'] for row in reveal['option_stats'] if row['is_correct']]
        self.assertEqual(correct, ['A'])
        self.assertEqual(reveal['answered_count'], 2)
        self.assertEqual(reveal['correct_count'], 1)
        self.assertEqual(reveal['unanswered_count'], 1)
        self.assertEqual(reveal['correct_answer_display'], 'A')

    def test_multiple_choice_increments_each_selected_letter(self):
        from .models import Answer, Player, Room
        from .utils import build_question_reveal

        room = Room.objects.create(code='111002', name='Multi Reveal')
        question = Question.objects.create(
            text='哪些是偶数？',
            question_type=Question.TYPE_MULTIPLE,
            option_a='2',
            option_b='3',
            option_c='4',
            option_d='5',
            correct_option='A,C',
        )
        self._attach(room, question)
        p1 = Player.objects.create(room=room, nickname='M1', session_id='m1')
        p2 = Player.objects.create(room=room, nickname='M2', session_id='m2')
        Answer.objects.create(
            room=room, player=p1, question=question,
            selected_option='A,C', is_correct=True, points=900, response_time_ms=300,
        )
        Answer.objects.create(
            room=room, player=p2, question=question,
            selected_option='A,B', is_correct=False, points=0, response_time_ms=400,
        )

        reveal = build_question_reveal(room, question)
        counts = {row['key']: row['count'] for row in reveal['option_stats']}
        self.assertEqual(counts['A'], 2)
        self.assertEqual(counts['B'], 1)
        self.assertEqual(counts['C'], 1)
        self.assertEqual(counts['D'], 0)
        self.assertEqual(reveal['correct_count'], 1)
        self.assertEqual(reveal['correct_answer_display'], 'A, C')

    def test_short_answer_counts_correct_and_shows_answer(self):
        from .models import Answer, Player, Room
        from .utils import build_question_reveal

        room = Room.objects.create(code='111003', name='Short Reveal')
        question = Question.objects.create(
            text='中国的首都？',
            question_type=Question.TYPE_SHORT_ANSWER,
            option_a='北京|Beijing',
            option_b='',
            option_c='',
            option_d='',
            correct_option='',
        )
        self._attach(room, question)
        p1 = Player.objects.create(room=room, nickname='S1', session_id='sa1')
        p2 = Player.objects.create(room=room, nickname='S2', session_id='sa2')
        Player.objects.create(room=room, nickname='S3', session_id='sa3')
        Answer.objects.create(
            room=room, player=p1, question=question,
            selected_option='北京', is_correct=True, points=700, response_time_ms=800,
        )
        Answer.objects.create(
            room=room, player=p2, question=question,
            selected_option='上海', is_correct=False, points=0, response_time_ms=900,
        )

        reveal = build_question_reveal(room, question)
        self.assertEqual(reveal['option_stats'], [])
        self.assertEqual(reveal['correct_count'], 1)
        self.assertEqual(reveal['answered_count'], 2)
        self.assertEqual(reveal['unanswered_count'], 1)
        self.assertEqual(reveal['correct_answer_display'], '北京 / Beijing')

    def test_runtime_records_feed_reveal_and_player_result(self):
        from .models import Room
        from .room_cache import drop_runtime, get_runtime, join_player, record_answer
        from .utils import build_question_reveal, get_my_result, get_room_state

        room = Room.objects.create(code='111004', name='Cache Reveal')
        question = Question.objects.create(
            text='1+1？',
            question_type=Question.TYPE_JUDGMENT,
            option_a='正确',
            option_b='错误',
            option_c='',
            option_d='',
            correct_option='A',
        )
        self._attach(room, question)
        runtime = get_runtime(room)
        join_player(runtime, 'Lee', 'sess-lee')
        join_player(runtime, 'Pat', 'sess-pat')
        record_answer(runtime, 'sess-lee', question.id, 'A', True, 500, 200)
        record_answer(runtime, 'sess-pat', question.id, 'B', False, 0, 300)

        reveal = build_question_reveal(room, question, runtime=runtime)
        counts = {row['key']: row['count'] for row in reveal['option_stats']}
        self.assertEqual(counts, {'A': 1, 'B': 1})
        self.assertEqual(reveal['player_count'], 2)

        mine = get_my_result(runtime, 'sess-lee', question.id)
        self.assertTrue(mine['answered'])
        self.assertTrue(mine['is_correct'])
        unanswered = get_my_result(runtime, 'sess-missing', question.id)
        self.assertFalse(unanswered['answered'])
        self.assertFalse(unanswered['is_correct'])

        room.status = Room.STATUS_LEADERBOARD
        room.current_question_index = 0
        room.save(update_fields=['status', 'current_question_index'])
        state = get_room_state(room, runtime=runtime)
        self.assertIn('reveal', state['question'])
        self.assertEqual(state['question']['reveal']['correct_count'], 1)
        drop_runtime(room.code)

    def test_host_reveal_template_has_chart_not_score_list(self):
        from django.template.loader import render_to_string
        from .models import Room

        room = Room.objects.create(code='111005', name='Host UI')
        html = render_to_string('game/room_host.html', {
            'room': room,
            'questions': [],
            'initial_state_json': '{}',
        })
        self.assertIn('host-reveal-chart', html)
        self.assertIn('结束本题', html)
        self.assertNotIn('结束本题 & 显示排行', html)
        self.assertNotIn('本题得分排行', html)
        self.assertNotIn('host-leaderboard-list', html)

    def test_student_template_waits_then_shows_dui_cuo(self):
        from django.template.loader import render_to_string
        from .models import Room

        room = Room.objects.create(code='111006', name='Play UI')
        html = render_to_string('game/play.html', {
            'room': room,
            'nickname': 'Test',
        })
        self.assertIn('已提交，等待揭晓', html)
        self.assertIn("title: isCorrect ? '对' : '错'", html)
        self.assertNotIn('回答正确', html)
        self.assertNotIn('回答错误', html)
        self.assertIn('applyStemMode', html)
        self.assertIn('play-hide-stem', html)


class StudentStemVisibilityTests(TestCase):
    def test_parse_show_question_stem(self):
        from .quiz_set_utils import parse_show_question_stem
        self.assertTrue(parse_show_question_stem({}))
        self.assertTrue(parse_show_question_stem({'show_question_stem': '1'}))
        self.assertFalse(parse_show_question_stem({'show_question_stem': '0'}))

    def test_create_room_can_hide_student_stem(self):
        from .models import QuizSet, QuizSetQuestion, Teacher
        from .quiz_set_utils import create_room_from_quiz_set
        from .utils import get_room_state

        teacher = Teacher.objects.create(username='t_stem')
        teacher.set_password('password123')
        teacher.save()
        quiz_set = QuizSet.objects.create(title='地理随堂', teacher=teacher)
        question = Question.objects.create(
            text='首都？',
            question_type=Question.TYPE_SINGLE,
            option_a='北京',
            option_b='上海',
            option_c='广州',
            option_d='深圳',
            correct_option='A',
        )
        QuizSetQuestion.objects.create(quiz_set=quiz_set, question=question, order=0)

        hidden = create_room_from_quiz_set(
            quiz_set, teacher, name='无题干局', show_question_stem=False,
        )
        shown = create_room_from_quiz_set(
            quiz_set, teacher, name='有题干局', show_question_stem=True,
        )
        self.assertFalse(hidden.show_question_stem)
        self.assertTrue(shown.show_question_stem)
        self.assertFalse(get_room_state(hidden)['show_question_stem'])
        self.assertTrue(get_room_state(shown)['show_question_stem'])

    def test_room_create_template_has_stem_choice(self):
        from django.template.loader import render_to_string

        html = render_to_string('game/room_create.html', {
            'my_quiz_sets': [],
            'public_quiz_sets': [],
            'show_question_stem': True,
        })
        self.assertIn('name="show_question_stem"', html)
        self.assertIn('不显示，只出选项', html)
        self.assertIn('显示题干和图片', html)


class KahootAIGenerateTests(TestCase):
    def setUp(self):
        from .models import Teacher
        self.teacher = Teacher.objects.create(username='t_ai')
        self.teacher.set_password('password123')
        self.teacher.save()
        session = self.client.session
        session['teacher_id'] = self.teacher.pk
        session['kahoot_pending_title'] = '地理测验'
        session.save()

    def test_ai_page_disables_turbo(self):
        from django.urls import reverse
        from unittest.mock import patch

        with patch('game.views.stepfun_configured', return_value=True):
            resp = self.client.get(reverse('kahoot_ai'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-turbo="false"')

    def test_generate_redirects_to_preview(self):
        from django.urls import reverse
        from unittest.mock import patch

        fake_questions = [{
            'text': '中国的首都是？',
            'question_type': 'single',
            'option_a': '北京',
            'option_b': '上海',
            'option_c': '广州',
            'option_d': '深圳',
            'correct_option': 'A',
            'time_limit': 20,
        }]
        with patch('game.views.stepfun_configured', return_value=True), patch(
            'game.views.generate_kahoot_questions', return_value=fake_questions,
        ):
            url = reverse('kahoot_ai')
            resp = self.client.post(url, {
                'topic': '地理',
                'description': '中等难度',
                'kahoot_title': '地理测验',
                'count_single': 1,
                'count_multiple': 0,
                'count_judgment': 0,
                'count_short_answer': 0,
            })
        self.assertRedirects(resp, url)
        follow = self.client.get(url)
        self.assertContains(follow, '中国的首都是？')
        self.assertContains(follow, '预览（1 道）')
        self.assertContains(follow, 'ai-loading-overlay hidden')






