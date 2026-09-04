from django.test import TestCase, override_settings

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
        self.assertIn('keycaps-stage', content)
        self.assertIn('6位数字PIN', content)
        self.assertIn('[0-9A-Za-z]{6}', content)

    def test_letter_code_unknown_keeps_landing(self):
        from django.urls import reverse
        resp = self.client.post(reverse('join_room'), {
            'code': 'ABCDEF',
            'nickname': 'TestUser',
        })
        self.assertEqual(resp.status_code, 422)
        self.assertContains(resp, '练习码不存在', status_code=422)
        self.assertContains(resp, 'keycaps-stage', status_code=422)

    def test_turbo_script_served_locally(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        self.assertIn('turbo.min.js', content)
        self.assertNotIn('https://cdn.jsdelivr.net/npm/@hotwired/turbo@8.0.12/dist/turbo.min.js', content)
        self.assertIn('turbo-cache-control', content)
        self.assertIn('no-cache', content)

    def test_bgm_disables_turbo_on_forms(self):
        from pathlib import Path
        from django.conf import settings
        bgm = (Path(settings.BASE_DIR) / 'static' / 'js' / 'bgm.js').read_text()
        self.assertIn('disableTurboOnForms', bgm)
        self.assertIn("form.setAttribute('data-turbo', 'false')", bgm)

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

    def test_playing_state_tracks_live_answered_count(self):
        from .models import Room
        from .room_cache import drop_runtime, get_runtime, join_player, record_answer
        from .utils import get_room_state

        room = Room.objects.create(
            code='111007',
            name='Live Count',
            status=Room.STATUS_PLAYING,
            current_question_index=0,
        )
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
        runtime = get_runtime(room)
        join_player(runtime, 'Lee', 'sess-lee')
        join_player(runtime, 'Pat', 'sess-pat')
        record_answer(runtime, 'sess-lee', question.id, 'A', True, 500, 200)

        state = get_room_state(room, runtime=runtime)
        self.assertEqual(state['player_count'], 2)
        self.assertEqual(state['answered_count'], 1)

        record_answer(runtime, 'sess-pat', question.id, 'B', False, 0, 300)
        state = get_room_state(room, runtime=runtime)
        self.assertEqual(state['answered_count'], 2)
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
        self.assertIn('host-question-countdown', html)
        self.assertIn('QuestionCountdown', html)
        self.assertIn('host-mid-leaderboard', html)
        self.assertIn('answers_updated', html)
        self.assertIn('updateHostAnswerProgress', html)
        self.assertIn('hostPlayingAction', html)
        self.assertIn('ranking_shown', html)
        self.assertIn("host.btn_show_ranking", html)
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
        self.assertIn("_t('fb.submitted')", html)
        self.assertIn("title: '未作答'", html)
        self.assertIn("_t('fb.correct')", html)
        self.assertIn("_t('fb.wrong')", html)
        self.assertNotIn('回答正确', html)
        self.assertNotIn('回答错误', html)
        self.assertIn('applyStemMode', html)
        self.assertIn('play-hide-stem', html)
        self.assertIn('play-show-stem', html)
        self.assertIn('question-countdown', html)
        self.assertIn('QuestionCountdown', html)
        self.assertIn('showPoints: true', html)
        self.assertIn('feedback-rank-board', html)
        self.assertIn("state.status === 'leaderboard'", html)
        self.assertIn('answer_rejected', html)
        self.assertIn('unlockAnswerUi', html)


class StudentStemVisibilityTests(TestCase):
    def test_parse_show_question_stem(self):
        from .quiz_set_utils import parse_show_question_stem
        self.assertTrue(parse_show_question_stem({}))
        self.assertTrue(parse_show_question_stem({'show_question_stem': '1'}))
        self.assertFalse(parse_show_question_stem({'show_question_stem': '0'}))

    def test_show_stem_css_keeps_options_tappable(self):
        from pathlib import Path
        from django.conf import settings

        css = (Path(settings.BASE_DIR) / 'static' / 'css' / 'style.css').read_text()
        self.assertIn('.play-screen.play-show-stem #options-container:not(.hidden)', css)
        self.assertIn('min-height: min(46vh, 22rem)', css)
        self.assertIn('min-height: 5.5rem', css)

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


def _tiny_png(name='slide.png'):
    from io import BytesIO

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    buf = BytesIO()
    Image.new('RGB', (16, 9), color=(20, 90, 180)).save(buf, format='PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


import tempfile


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class ExplanationQuestionTests(TestCase):
    def _make_explanation(self, with_image=True) -> Question:
        q = Question(
            text=Question.EXPLANATION_TEXT_PLACEHOLDER,
            question_type=Question.TYPE_EXPLANATION,
            option_a=Question.TEXT_OPTION_PLACEHOLDER,
            option_b=Question.TEXT_OPTION_PLACEHOLDER,
            option_c=Question.TEXT_OPTION_PLACEHOLDER,
            option_d=Question.TEXT_OPTION_PLACEHOLDER,
            correct_option='',
            time_limit=30,
        )
        if with_image:
            q.image = _tiny_png()
        q.save()
        return q

    def test_unscored_and_not_answerable(self):
        q = self._make_explanation()
        self.assertTrue(q.is_unscored())
        self.assertFalse(q.is_answer_correct('A'))
        self.assertEqual(q.get_options(), [])
        self.assertEqual(q.get_correct_option_display(), '')

    def test_parse_requires_image(self):
        from django.test import RequestFactory

        from .question_save import QuestionFormError, parse_question_from_request

        factory = RequestFactory()
        request = factory.post('/', {'question_type': 'explanation', 'time_limit': '20'})
        with self.assertRaises(QuestionFormError):
            parse_question_from_request(request)

        request = factory.post('/', {
            'question_type': 'explanation',
            'time_limit': '45',
            'text': 'ignored',
            'image': _tiny_png(),
        })
        fields = parse_question_from_request(request)
        self.assertEqual(fields['question_type'], Question.TYPE_EXPLANATION)
        self.assertEqual(fields['text'], Question.EXPLANATION_TEXT_PLACEHOLDER)
        self.assertTrue(fields['image_file'])
        self.assertEqual(fields['time_limit'], 0)

    def test_room_state_is_fullscreen_slide(self):
        from .models import Room, RoomQuestion
        from .utils import get_room_state
        from django.utils import timezone

        question = self._make_explanation()
        room = Room.objects.create(
            code='112233',
            name='讲解房',
            status=Room.STATUS_PLAYING,
            current_question_index=0,
            question_started_at=timezone.now(),
        )
        RoomQuestion.objects.create(room=room, question=question, order=0)
        state = get_room_state(room)
        self.assertEqual(state['question']['question_type'], Question.TYPE_EXPLANATION)
        self.assertTrue(state['question']['no_score'])
        self.assertTrue(state['question'].get('image_url'))
        self.assertEqual(state['question']['options'], [])
        self.assertEqual(state['countdown_remaining_ms'], 0)

    def test_analytics_skips_explanation_for_players(self):
        from .analytics import get_room_analytics_data
        from .models import Player, Room, RoomQuestion

        question = self._make_explanation()
        scored = Question.objects.create(
            text='1+1?',
            question_type=Question.TYPE_SINGLE,
            option_a='2', option_b='3', option_c='4', option_d='5',
            correct_option='A',
        )
        room = Room.objects.create(code='334455', name='Analytics Exp')
        RoomQuestion.objects.create(room=room, question=question, order=0)
        RoomQuestion.objects.create(room=room, question=scored, order=1)
        Player.objects.create(room=room, nickname='Ann', session_id='ann', score=0)
        data = get_room_analytics_data(room)
        by_q = data['by_questions']
        self.assertEqual(by_q[0]['is_explanation'], True)
        self.assertEqual(by_q[0]['is_unscored'], True)
        self.assertEqual(data['summary']['total_scored_questions'], 1)
        self.assertEqual(data['by_players'][0]['unanswered_count'], 1)

    def test_editor_save_api(self):
        from django.urls import reverse

        from .models import QuizSet, Teacher

        teacher = Teacher.objects.create(username='t_explain')
        teacher.set_password('password123')
        teacher.save()
        quiz_set = QuizSet.objects.create(title='讲解套题', teacher=teacher)
        session = self.client.session
        session['teacher_id'] = teacher.pk
        session.save()

        add_url = reverse('kahoot_question_add', args=[quiz_set.pk])
        add_resp = self.client.post(add_url)
        self.assertEqual(add_resp.status_code, 200)
        qid = add_resp.json()['question']['id']

        save_url = reverse('kahoot_question_save', args=[quiz_set.pk])
        resp = self.client.post(save_url, {
            'question_id': qid,
            'question_type': 'explanation',
            'time_limit': '60',
            'image': _tiny_png(),
        })
        self.assertEqual(resp.status_code, 200, resp.content)
        data = resp.json()['question']
        self.assertEqual(data['question_type'], 'explanation')
        self.assertTrue(data['image_url'])
        self.assertEqual(data['text'], Question.EXPLANATION_TEXT_PLACEHOLDER)
        self.assertEqual(data['time_limit'], 0)

    def test_clone_copies_explanation_image(self):
        from .models import QuizSet, Teacher
        from .quiz_set_utils import add_question_to_quiz_set, clone_quiz_set

        owner = Teacher.objects.create(username='t_src')
        owner.set_password('password123')
        owner.save()
        other = Teacher.objects.create(username='t_dst')
        other.set_password('password123')
        other.save()
        source = QuizSet.objects.create(title='带讲解', teacher=owner, is_public=True)
        question = self._make_explanation()
        question.teacher = owner
        question.save(update_fields=['teacher'])
        add_question_to_quiz_set(source, question)

        cloned = clone_quiz_set(source, other, '带讲解副本')
        cloned_q = cloned.get_questions()[0]
        self.assertEqual(cloned_q.question_type, Question.TYPE_EXPLANATION)
        self.assertTrue(cloned_q.image)
        self.assertNotEqual(cloned_q.image.name, question.image.name)


class QuestionCountdownTests(TestCase):
    def test_remaining_ms_from_start_time(self):
        from datetime import timedelta

        from django.utils import timezone

        from .models import Room
        from .utils import QUESTION_COUNTDOWN_SECONDS, can_accept_answer, question_countdown_remaining_ms

        started = timezone.now()
        room = Room.objects.create(
            code='445566',
            name='Countdown',
            status=Room.STATUS_PLAYING,
            question_started_at=started,
        )
        self.assertEqual(QUESTION_COUNTDOWN_SECONDS, 3)
        self.assertEqual(question_countdown_remaining_ms(room, now=started), 3000)
        self.assertEqual(
            question_countdown_remaining_ms(room, now=started + timedelta(milliseconds=1200)),
            1800,
        )
        self.assertEqual(
            question_countdown_remaining_ms(room, now=started + timedelta(seconds=3)),
            0,
        )
        self.assertFalse(can_accept_answer(room))
        room.question_started_at = started - timedelta(seconds=4)
        room.save(update_fields=['question_started_at'])
        self.assertTrue(can_accept_answer(room))

        room.status = Room.STATUS_WAITING
        room.save(update_fields=['status'])
        self.assertEqual(question_countdown_remaining_ms(room, now=started), 0)
        self.assertFalse(can_accept_answer(room))

    def test_explanation_question_skips_countdown_without_orm(self):
        from django.utils import timezone

        from .models import Question, Room
        from .utils import can_accept_answer, question_countdown_remaining_ms

        started = timezone.now()
        room = Room.objects.create(
            code='445577',
            name='Explain CD',
            status=Room.STATUS_PLAYING,
            question_started_at=started,
        )
        slide = Question(
            question_type=Question.TYPE_EXPLANATION,
            time_limit=0,
        )
        self.assertEqual(question_countdown_remaining_ms(room, now=started, question=slide), 0)
        self.assertTrue(can_accept_answer(room, slide))

    def test_room_state_includes_countdown(self):
        from django.utils import timezone

        from .models import Room, RoomQuestion
        from .utils import get_room_state

        question = Question.objects.create(
            text='首都？',
            question_type=Question.TYPE_SINGLE,
            option_a='北京',
            option_b='上海',
            option_c='广州',
            option_d='深圳',
            correct_option='A',
        )
        started = timezone.now()
        room = Room.objects.create(
            code='778899',
            name='Countdown State',
            status=Room.STATUS_PLAYING,
            current_question_index=0,
            question_started_at=started,
        )
        RoomQuestion.objects.create(room=room, question=question, order=0)
        state = get_room_state(room)
        self.assertEqual(state['countdown_seconds'], 3)
        self.assertGreater(state['countdown_remaining_ms'], 2000)
        self.assertLessEqual(state['countdown_remaining_ms'], 3000)


class TeacherSettingsTests(TestCase):
    def setUp(self):
        from .models import Teacher
        self.teacher = Teacher.objects.create(username='t_settings', display_name='老师甲')
        self.teacher.set_password('oldpass1')
        self.teacher.save()
        session = self.client.session
        session['teacher_id'] = self.teacher.pk
        session.save()

    def test_dashboard_has_settings_entry(self):
        from django.urls import reverse
        resp = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'btn-open-settings')
        self.assertContains(resp, 'settings-overlay')
        self.assertContains(resp, 'teacher-settings-form')
        self.assertContains(resp, '布置练习')
        self.assertContains(resp, reverse('practice_assign'))
        self.assertContains(resp, reverse('room_create'))

    def test_update_profile_without_password(self):
        import json

        from django.urls import reverse

        from .models import Teacher
        resp = self.client.post(
            reverse('teacher_settings'),
            data=json.dumps({
                'display_name': '地理老师',
                'gender': 'female',
                'username': 't_settings',
                'avatar': {'face': 3, 'hair': 2},
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        payload = resp.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['teacher']['display_name'], '地理老师')
        self.assertEqual(payload['teacher']['gender'], 'female')
        self.assertEqual(payload['teacher']['avatar'], {'face': 3, 'hair': 2})
        teacher = Teacher.objects.get(pk=self.teacher.pk)
        self.assertEqual(teacher.display_name, '地理老师')
        self.assertEqual(teacher.gender, 'female')

    def test_username_change_requires_password(self):
        import json

        from django.urls import reverse
        resp = self.client.post(
            reverse('teacher_settings'),
            data=json.dumps({
                'display_name': '老师甲',
                'gender': 'unspecified',
                'username': 'new_teacher',
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.username, 't_settings')

    def test_password_change(self):
        import json

        from django.urls import reverse

        from .models import Teacher
        resp = self.client.post(
            reverse('teacher_settings'),
            data=json.dumps({
                'display_name': '老师甲',
                'gender': 'unspecified',
                'username': 't_settings',
                'current_password': 'oldpass1',
                'new_password': 'newpass9',
                'new_password_confirm': 'newpass9',
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        teacher = Teacher.objects.get(pk=self.teacher.pk)
        self.assertTrue(teacher.check_password('newpass9'))
        self.assertFalse(teacher.check_password('oldpass1'))


class RevealThenRankingFlowTests(TestCase):
    def _choice_question(self):
        return Question.objects.create(
            text='首都？',
            question_type=Question.TYPE_SINGLE,
            option_a='北京',
            option_b='上海',
            option_c='广州',
            option_d='深圳',
            correct_option='A',
            time_limit=20,
        )

    def _explanation(self):
        q = Question(
            text=Question.EXPLANATION_TEXT_PLACEHOLDER,
            question_type=Question.TYPE_EXPLANATION,
            option_a=Question.TEXT_OPTION_PLACEHOLDER,
            option_b=Question.TEXT_OPTION_PLACEHOLDER,
            option_c=Question.TEXT_OPTION_PLACEHOLDER,
            option_d=Question.TEXT_OPTION_PLACEHOLDER,
            correct_option='',
            time_limit=0,
        )
        q.image = _tiny_png()
        q.save()
        return q

    def test_end_question_shows_stats_then_ranking_then_next(self):
        from .consumers import advance_question_for_room, end_question_for_room
        from .models import Room, RoomQuestion

        q1 = self._choice_question()
        q2 = self._choice_question()
        q2.text = '第二题'
        q2.save(update_fields=['text'])
        room = Room.objects.create(
            code='221001',
            name='两步揭晓',
            status=Room.STATUS_PLAYING,
            current_question_index=0,
        )
        RoomQuestion.objects.create(room=room, question=q1, order=0)
        RoomQuestion.objects.create(room=room, question=q2, order=1)

        state, event = end_question_for_room(room.code)
        self.assertEqual(event, 'question_ended')
        self.assertEqual(state['status'], Room.STATUS_REVEAL)
        self.assertIn('reveal', state['question'])

        state, event, error = advance_question_for_room(room.code)
        self.assertIsNone(error)
        self.assertEqual(event, 'ranking_shown')
        self.assertEqual(state['status'], Room.STATUS_LEADERBOARD)
        self.assertIn('reveal', state['question'])

        state, event, error = advance_question_for_room(room.code)
        self.assertIsNone(error)
        self.assertEqual(event, 'question_started')
        self.assertEqual(state['status'], Room.STATUS_PLAYING)
        self.assertEqual(state['current_question_index'], 1)
        self.assertEqual(state['question']['id'], q2.id)

    def test_explanation_skips_stats_and_ranking(self):
        from .consumers import advance_question_for_room, end_question_for_room
        from .models import Room, RoomQuestion

        slide = self._explanation()
        q2 = self._choice_question()
        room = Room.objects.create(
            code='221002',
            name='讲解跳过',
            status=Room.STATUS_PLAYING,
            current_question_index=0,
        )
        RoomQuestion.objects.create(room=room, question=slide, order=0)
        RoomQuestion.objects.create(room=room, question=q2, order=1)

        state, event, error = advance_question_for_room(room.code)
        self.assertIsNone(error)
        self.assertEqual(event, 'question_started')
        self.assertEqual(state['status'], Room.STATUS_PLAYING)
        self.assertEqual(state['question']['id'], q2.id)

        room.status = Room.STATUS_PLAYING
        room.current_question_index = 0
        room.save(update_fields=['status', 'current_question_index'])
        state, event = end_question_for_room(room.code)
        self.assertEqual(event, 'question_started')
        self.assertEqual(state['status'], Room.STATUS_PLAYING)
        self.assertEqual(state['question']['id'], q2.id)

    def test_last_explanation_ends_game(self):
        from .consumers import advance_question_for_room
        from .models import Room, RoomQuestion

        slide = self._explanation()
        room = Room.objects.create(
            code='221003',
            name='最后一题讲解',
            status=Room.STATUS_PLAYING,
            current_question_index=0,
        )
        RoomQuestion.objects.create(room=room, question=slide, order=0)
        state, event, error = advance_question_for_room(room.code)
        self.assertIsNone(error)
        self.assertEqual(event, 'game_ended')
        self.assertEqual(state['status'], Room.STATUS_ENDED)


class ClickThroughSafetyTests(TestCase):
    def test_language_switcher_uses_document_delegation(self):
        from pathlib import Path

        from django.conf import settings

        js = (Path(settings.BASE_DIR) / 'static' / 'js' / 'i18n.js').read_text()
        self.assertIn("closest('[data-action=\"toggle-lang\"]')", js)
        self.assertIn("document.addEventListener('click'", js)
        self.assertIn('_langDelegated', js)
        self.assertIn('turbo:load', js)
        self.assertIn('csrf-token', js)
        self.assertNotIn(
            "querySelectorAll('[data-action=\"toggle-lang\"]').forEach",
            js,
        )

    def test_hidden_overlays_cannot_intercept_clicks(self):
        from pathlib import Path

        from django.conf import settings

        css = (Path(settings.BASE_DIR) / 'static' / 'css' / 'style.css').read_text()
        self.assertIn('.q-countdown.hidden', css)
        self.assertIn('.practice-copy-toast.hidden', css)
        self.assertIn('.play-feedback-stage.hidden', css)
        self.assertIn('.settings-overlay.hidden', css)
        self.assertIn('.ai-loading-overlay.hidden', css)
        self.assertIn('pointer-events: none !important', css)
        self.assertIn('.q-countdown:not(.hidden)', css)
        self.assertIn('.landing-main-flow', css)
        self.assertIn('.turbo-progress-bar', css)
        self.assertIn('.btn-lang-toggle', css)
        self.assertIn('pointer-events: none !important', css)

        editor_css = (Path(settings.BASE_DIR) / 'static' / 'css' / 'kahoot_editor.css').read_text()
        self.assertIn('.modal-overlay.hidden', editor_css)
        self.assertIn('pointer-events: none !important', editor_css)

        countdown = (Path(settings.BASE_DIR) / 'static' / 'js' / 'question_countdown.js').read_text()
        self.assertIn("el.setAttribute('inert', '')", countdown)
        self.assertIn("el.removeAttribute('inert')", countdown)

        bgm = (Path(settings.BASE_DIR) / 'static' / 'js' / 'bgm.js').read_text()
        self.assertIn('setTimeout(recoverStuckTurbo, 2000)', bgm)

    def test_base_template_exposes_csrf_and_cache_bust(self):
        from django.template.loader import render_to_string
        from django.test import RequestFactory

        request = RequestFactory().get('/')
        html = render_to_string('base.html', request=request)
        self.assertIn('name="csrf-token"', html)
        self.assertIn('csrfmiddlewaretoken', html)
        self.assertIn('style.css?v=473', html)
        self.assertIn('i18n.js?v=12', html)
        self.assertIn('data-action="toggle-lang"', html)


class PublicQuizLibraryTests(TestCase):
    def setUp(self):
        from .models import Question, QuizSet, QuizSetQuestion, Teacher

        self.owner = Teacher.objects.create(username='pub_owner', display_name='地理老师')
        self.owner.set_password('password123')
        self.owner.save()
        self.viewer = Teacher.objects.create(username='pub_viewer')
        self.viewer.set_password('password123')
        self.viewer.save()

        self.quiz = QuizSet.objects.create(
            title='亚洲地理公开课',
            teacher=self.owner,
            is_public=True,
        )
        self.question = Question.objects.create(
            text='中国的首都是？',
            question_type=Question.TYPE_SINGLE,
            option_a='北京',
            option_b='上海',
            option_c='广州',
            option_d='深圳',
            correct_option='A',
            teacher=self.owner,
        )
        QuizSetQuestion.objects.create(quiz_set=self.quiz, question=self.question, order=0)
        from .practice_utils import ensure_practice_code
        ensure_practice_code(self.quiz)

        self.private = QuizSet.objects.create(
            title='私有套题',
            teacher=self.owner,
            is_public=False,
        )
        session = self.client.session
        session['teacher_id'] = self.viewer.pk
        session.save()

    def test_list_shows_search_and_preview(self):
        from django.urls import reverse

        resp = self.client.get(reverse('kahoot_public_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="public-quiz-search"')
        self.assertContains(resp, '亚洲地理公开课')
        self.assertContains(resp, reverse('kahoot_public_preview', args=[self.quiz.pk]))
        self.assertContains(resp, '预览')
        self.assertContains(resp, self.quiz.practice_code)
        self.assertContains(resp, '复制发给学生')
        self.assertNotContains(resp, '私有套题')

    def test_assign_practice_from_dashboard(self):
        from django.urls import reverse

        page = self.client.get(reverse('practice_assign'))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, '布置练习')
        self.assertContains(page, '返回控制台')
        self.assertContains(page, '亚洲地理公开课')
        self.assertContains(page, self.quiz.practice_code)
        self.assertContains(page, '复制发给学生')
        self.assertContains(page, 'data-copy-kind="share"')
        self.assertContains(page, reverse('teacher_dashboard'))
        self.assertNotContains(page, '复制到我的题库')
        preview = self.client.get(
            reverse('kahoot_public_preview', args=[self.quiz.pk]),
            {'from': 'assign'},
        )
        self.assertContains(preview, '返回布置练习')
        self.assertContains(preview, reverse('practice_assign'))

    def test_search_matches_title_author_and_question_text(self):
        from django.urls import reverse

        url = reverse('kahoot_public_list')
        by_title = self.client.get(url, {'q': '亚洲地理'})
        self.assertContains(by_title, '亚洲地理公开课')

        by_author = self.client.get(url, {'q': '地理老师'})
        self.assertContains(by_author, '亚洲地理公开课')

        by_stem = self.client.get(url, {'q': '首都'})
        self.assertContains(by_stem, '亚洲地理公开课')

        by_option = self.client.get(url, {'q': '北京'})
        self.assertContains(by_option, '亚洲地理公开课')

        miss = self.client.get(url, {'q': '不存在的关键词xyz'})
        self.assertNotContains(miss, '亚洲地理公开课')
        self.assertContains(miss, '没有找到匹配的套题')

    def test_preview_shows_questions_and_blocks_private(self):
        from django.urls import reverse

        resp = self.client.get(reverse('kahoot_public_preview', args=[self.quiz.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '中国的首都是？')
        self.assertContains(resp, '北京')
        self.assertContains(resp, '复制到我的题库')
        self.assertContains(resp, 'is-correct')

        blocked = self.client.get(reverse('kahoot_public_preview', args=[self.private.pk]))
        self.assertEqual(blocked.status_code, 302)
        self.assertEqual(blocked.url, reverse('kahoot_public_list'))

    def test_wizard_public_action_opens_marketplace(self):
        from django.urls import reverse

        resp = self.client.post(reverse('kahoot_start'), {
            'action': 'public',
            'title': '随便起的名字',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('kahoot_public_list'))

    def test_seed_command_creates_marketplace_quizzes(self):
        from io import StringIO

        from django.core.management import call_command
        from django.urls import reverse

        from .models import Question, QuizSet

        out = StringIO()
        call_command('seed_public_quizzes', stdout=out)
        call_command('seed_public_quizzes', stdout=out)
        self.assertGreaterEqual(
            QuizSet.objects.filter(is_public=True, teacher__username='kahoot_market').count(),
            6,
        )
        resp = self.client.get(reverse('kahoot_public_list'))
        self.assertContains(resp, '世界地理入门')
        self.assertContains(resp, '小学数学口算')
        self.assertContains(resp, '中国历史常识')
        self.assertContains(resp, '科学判断小测验')
        self.assertContains(resp, '趣味英语词汇')
        self.assertContains(resp, '课堂暖场词云')
        self.assertContains(resp, '题库精选')
        self.assertTrue(
            Question.objects.filter(
                teacher__username='kahoot_market',
                question_type=Question.TYPE_WORD_CLOUD,
                text='用一个词形容今天的心情',
            ).exists()
        )
        self.assertTrue(
            QuizSet.objects.filter(is_public=True, teacher__username='kahoot_market')
            .exclude(practice_code='')
            .exclude(practice_code__isnull=True)
            .exists()
        )


class PracticeModeTests(TestCase):
    def setUp(self):
        from .models import Question, QuizSet, QuizSetQuestion, Teacher
        from .practice_utils import ensure_practice_code

        self.owner = Teacher.objects.create(username='practice_owner')
        self.owner.set_password('password123')
        self.owner.save()
        self.quiz = QuizSet.objects.create(
            title='练习地理',
            teacher=self.owner,
            is_public=True,
        )
        self.q1 = Question.objects.create(
            text='中国的首都是？',
            question_type=Question.TYPE_SINGLE,
            option_a='北京',
            option_b='上海',
            option_c='广州',
            option_d='深圳',
            correct_option='A',
            time_limit=20,
            teacher=self.owner,
        )
        self.q2 = Question.objects.create(
            text='1+1=？',
            question_type=Question.TYPE_SINGLE,
            option_a='1',
            option_b='2',
            option_c='3',
            option_d='4',
            correct_option='B',
            time_limit=15,
            teacher=self.owner,
        )
        QuizSetQuestion.objects.create(quiz_set=self.quiz, question=self.q1, order=0)
        QuizSetQuestion.objects.create(quiz_set=self.quiz, question=self.q2, order=1)
        self.code = ensure_practice_code(self.quiz)

    def test_join_letter_code_opens_practice(self):
        from django.urls import reverse

        resp = self.client.post(reverse('join_room'), {
            'code': self.code.lower(),
            'nickname': '练习生',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('practice_play', args=[self.code]))
        follow = self.client.get(resp.url)
        self.assertEqual(follow.status_code, 200)
        self.assertContains(follow, '开始练习')
        self.assertContains(follow, '练习地理')
        self.assertNotContains(follow, '等待老师开始游戏')
        html = follow.content.decode()
        self.assertIn('window.PRACTICE_BOOT', html)
        self.assertLess(
            html.find('window.PRACTICE_BOOT'),
            html.find('js/practice.js'),
        )
        self.assertIn(reverse('practice_start', args=[self.code]), html)

    def test_digit_pin_still_joins_live_room(self):
        from django.urls import reverse

        from .models import Room

        room = Room.objects.create(code='654321', name='直播房')
        resp = self.client.post(reverse('join_room'), {
            'code': '654321',
            'nickname': '学生甲',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('play', args=['654321']))

    def test_practice_scores_and_leaderboard(self):
        import json

        from django.urls import reverse

        from .models import PracticeAttempt

        self.client.post(reverse('join_room'), {
            'code': self.code,
            'nickname': 'Ace',
        })
        start = self.client.post(
            reverse('practice_start', args=[self.code]),
            data=json.dumps({'avatar': {'face': 1, 'hair': 2}}),
            content_type='application/json',
        )
        self.assertEqual(start.status_code, 200)
        token = start.json()['token']
        quiz_payload = start.json()['quiz']
        self.assertEqual(len(quiz_payload['questions']), 2)
        self.assertNotIn('correct_option', quiz_payload['questions'][0])

        ans1 = self.client.post(
            reverse('practice_answer', args=[self.code]),
            data=json.dumps({
                'token': token,
                'question_id': self.q1.id,
                'selected': 'A',
                'response_time_ms': 1000,
            }),
            content_type='application/json',
        )
        self.assertEqual(ans1.status_code, 200)
        self.assertTrue(ans1.json()['is_correct'])
        self.assertGreater(ans1.json()['points'], 0)

        ans2 = self.client.post(
            reverse('practice_answer', args=[self.code]),
            data=json.dumps({
                'token': token,
                'question_id': self.q2.id,
                'selected': 'A',
                'response_time_ms': 500,
            }),
            content_type='application/json',
        )
        self.assertFalse(ans2.json()['is_correct'])

        done = self.client.post(
            reverse('practice_finish', args=[self.code]),
            data=json.dumps({'token': token}),
            content_type='application/json',
        )
        self.assertEqual(done.status_code, 200)
        self.assertEqual(done.json()['score'], ans1.json()['points'])
        self.assertEqual(done.json()['leaderboard'][0]['nickname'], 'Ace')
        self.assertEqual(PracticeAttempt.objects.filter(quiz_set=self.quiz).count(), 1)

    def test_classify_join_code(self):
        from .practice_utils import classify_join_code
        self.assertEqual(classify_join_code('123456'), ('pin', '123456'))
        self.assertEqual(classify_join_code('abCdef'), ('practice', 'ABCDEF'))
        self.assertEqual(classify_join_code('AB12CD')[0], 'invalid')


class WordCloudAggregationTests(TestCase):
    def test_merges_case_and_whitespace(self):
        from .word_cloud import collapse_word_cloud_texts

        words = collapse_word_cloud_texts(['Happy', 'happy', ' HAPPY ', 'joy', 'Joy', '  '])
        by_key = {item['text'].casefold(): item for item in words}
        self.assertEqual(by_key['happy']['count'], 3)
        self.assertEqual(by_key['joy']['count'], 2)
        self.assertEqual(by_key['happy']['text'], 'Happy')

        punct = collapse_word_cloud_texts(['开心！', '开心', '开心。', '!!!'])
        self.assertEqual(len(punct), 1)
        self.assertEqual(punct[0]['text'], '开心')
        self.assertEqual(punct[0]['count'], 3)

    def test_live_pending_does_not_double_count_flushed_answer(self):
        from .models import Answer, Player, Room
        from .room_cache import PendingAnswer, drop_runtime, get_runtime, join_player
        from .word_cloud import aggregate_word_cloud

        room = Room.objects.create(code='888001', name='Cloud Room')
        question = Question.objects.create(
            text='用一个词形容今天',
            question_type=Question.TYPE_WORD_CLOUD,
            option_a='', option_b='', option_c='', option_d='',
            correct_option='',
        )
        from .models import RoomQuestion
        RoomQuestion.objects.create(room=room, question=question, order=0)
        drop_runtime(room.code)
        runtime = get_runtime(room)
        join_player(runtime, 'Ada', 'sess-ada')
        from .room_cache import flush_runtime_force
        flush_runtime_force(runtime)
        player = Player.objects.get(session_id='sess-ada')
        Answer.objects.create(
            room=room, player=player, question=question,
            selected_option='Happy', is_correct=False, points=0, response_time_ms=200,
        )
        runtime.pending_answers.append(PendingAnswer(
            session_id='sess-ada',
            question_id=question.id,
            selected='happy',
            is_correct=False,
            points=0,
            response_time_ms=200,
        ))
        cloud = aggregate_word_cloud(room.code, question.id, runtime)
        self.assertEqual(len(cloud), 1)
        self.assertEqual(cloud[0]['count'], 1)
        drop_runtime(room.code)

    def test_practice_word_cloud_roundtrip(self):
        import json

        from django.urls import reverse

        from .models import QuizSet, Teacher
        from .practice_utils import ensure_practice_code
        from .quiz_set_utils import add_question_to_quiz_set

        teacher = Teacher.objects.create(username='cloud_teacher')
        quiz = QuizSet.objects.create(title='词云练习', teacher=teacher, is_public=True)
        question = Question.objects.create(
            text='用一个词形容春天',
            question_type=Question.TYPE_WORD_CLOUD,
            option_a='', option_b='', option_c='', option_d='',
            correct_option='', teacher=teacher,
        )
        add_question_to_quiz_set(quiz, question)
        code = ensure_practice_code(quiz)

        self.client.post(reverse('join_room'), {'code': code, 'nickname': '春游'})
        start = self.client.post(
            reverse('practice_start', args=[code]),
            data=json.dumps({'avatar': {'face': 0, 'hair': 0}}),
            content_type='application/json',
        )
        token = start.json()['token']
        empty = self.client.post(
            reverse('practice_answer', args=[code]),
            data=json.dumps({
                'token': token, 'question_id': question.id,
                'selected': '   ', 'response_time_ms': 100,
            }),
            content_type='application/json',
        )
        self.assertEqual(empty.status_code, 400)

        answered = self.client.post(
            reverse('practice_answer', args=[code]),
            data=json.dumps({
                'token': token, 'question_id': question.id,
                'selected': 'Warm', 'response_time_ms': 400,
            }),
            content_type='application/json',
        )
        self.assertEqual(answered.status_code, 200)
        self.assertTrue(answered.json()['no_score'])
        self.assertEqual(answered.json()['word_cloud'][0]['text'], 'Warm')
        self.assertEqual(answered.json()['word_cloud'][0]['count'], 1)

        other = self.client_class()
        other.post(reverse('join_room'), {'code': code, 'nickname': '同学'})
        start2 = other.post(
            reverse('practice_start', args=[code]),
            data=json.dumps({'avatar': {'face': 1, 'hair': 1}}),
            content_type='application/json',
        )
        token2 = start2.json()['token']
        other.post(
            reverse('practice_answer', args=[code]),
            data=json.dumps({
                'token': token2, 'question_id': question.id,
                'selected': 'warm', 'response_time_ms': 300,
            }),
            content_type='application/json',
        )
        done = other.post(
            reverse('practice_finish', args=[code]),
            data=json.dumps({'token': token2}),
            content_type='application/json',
        )
        clouds = done.json()['word_clouds']
        self.assertEqual(len(clouds), 1)
        self.assertEqual(clouds[0]['words'][0]['count'], 2)

    def test_play_and_host_templates_include_cloud_ui(self):
        from django.template.loader import render_to_string

        from .models import Room

        room = Room.objects.create(code='888002', name='Host Cloud')
        play = render_to_string('game/play.html', {
            'room': room,
            'nickname': 'Ada',
            'initial_state_json': '{}',
        })
        self.assertIn('play-word-cloud-wrap', play)
        self.assertIn('js/wordcloud.js?v=5', play)
        self.assertIn('word_cloud_updated', play)

        host = render_to_string('game/room_host.html', {
            'room': room,
            'questions': [],
            'initial_state_json': '{}',
        })
        self.assertIn('host-word-cloud-display', host)
        self.assertIn('js/wordcloud.js?v=5', host)

