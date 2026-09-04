"""End-to-end product feature QA: register, publish, host, join, practice."""

from __future__ import annotations

import json

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from io import StringIO

from .excel_import import build_template_xlsx, import_quiz_set_from_xlsx
from .models import (
    PracticeAttempt,
    Question,
    QuizSet,
    Room,
    Teacher,
    TeacherInviteCode,
)
from .practice_utils import classify_join_code, ensure_practice_code, practice_leaderboard
from .quiz_set_utils import create_room_from_quiz_set
from .consumers import start_game_for_room
from .utils import get_room_state


class FullProductFeatureQA(TestCase):
    """Walk every major product surface as a teacher + two students."""

    def setUp(self):
        self.invite = TeacherInviteCode.objects.create(code='QA2026', max_uses=3, note='feature qa')

    def _login(self, username, password):
        return self.client.post(reverse('teacher_login'), {
            'username': username,
            'password': password,
        })

    def test_01_landing_and_join_guards(self):
        home = self.client.get('/')
        self.assertEqual(home.status_code, 200)
        html = home.content.decode()
        self.assertIn('keycaps-stage', html)
        self.assertIn('6位数字PIN / 6位字母练习码', html)
        self.assertIn('[0-9A-Za-z]{6}', html)
        self.assertIn('登录老师控制台', html)
        self.assertIn('邀请码注册', html)
        self.assertIn('切换至老师端', html)
        self.assertIn('data-action="toggle-lang"', html)
        self.assertIn('turbo.min.js', html)

        missing = self.client.post(reverse('join_room'), {'code': '', 'nickname': ''})
        self.assertEqual(missing.status_code, 422)
        self.assertContains(missing, '请输入房间号/练习码和昵称', status_code=422)

        mixed = self.client.post(reverse('join_room'), {'code': 'AB12CD', 'nickname': '学生'})
        self.assertContains(mixed, '6 位数字房间号', status_code=422)

        ghost_pin = self.client.post(reverse('join_room'), {'code': '000000', 'nickname': '学生'})
        self.assertContains(ghost_pin, '房间号不存在', status_code=422)

        ghost_letter = self.client.post(reverse('join_room'), {'code': 'ABCDEF', 'nickname': '学生'})
        self.assertContains(ghost_letter, '练习码不存在', status_code=422)
        self.assertContains(ghost_letter, 'keycaps-stage', status_code=422)

        self.assertEqual(classify_join_code('123456'), ('pin', '123456'))
        self.assertEqual(classify_join_code('abCdef'), ('practice', 'ABCDEF'))
        self.assertEqual(classify_join_code('AB12CD')[0], 'invalid')

        lang = self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/'})
        self.assertIn(lang.status_code, (200, 302))

    def test_02_teacher_register_login_settings_logout(self):
        page = self.client.get(reverse('teacher_register'))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, '邀请码')

        bad_invite = self.client.post(reverse('teacher_register'), {
            'invite_code': 'NOPE',
            'username': 'qa_teacher',
            'password': 'secret123',
            'password_confirm': 'secret123',
        })
        self.assertEqual(bad_invite.status_code, 200)
        self.assertFalse(Teacher.objects.filter(username='qa_teacher').exists())
        self.assertContains(bad_invite, '邀请码无效')
        self.assertContains(bad_invite, 'join-inline-error')

        short_pw = self.client.post(reverse('teacher_register'), {
            'invite_code': 'QA2026',
            'username': 'qa_teacher',
            'password': '12',
            'password_confirm': '12',
        })
        self.assertEqual(short_pw.status_code, 200)
        self.assertFalse(Teacher.objects.filter(username='qa_teacher').exists())
        self.assertContains(short_pw, 'join-inline-error')
        self.assertContains(short_pw, '密码至少')

        ok = self.client.post(reverse('teacher_register'), {
            'invite_code': 'QA2026',
            'username': 'qa_teacher',
            'password': 'secret123',
            'password_confirm': 'secret123',
        })
        self.assertEqual(ok.status_code, 302)
        self.assertEqual(ok.url, reverse('teacher_dashboard'))
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.used_count, 1)

        dash = self.client.get(reverse('teacher_dashboard'))
        self.assertContains(dash, '发起新房间')
        self.assertContains(dash, '布置练习')
        self.assertContains(dash, '新建 Kahoot')
        self.assertContains(dash, '管理我的题库')
        self.assertContains(dash, 'btn-open-settings')

        settings = self.client.post(
            reverse('teacher_settings'),
            data=json.dumps({
                'display_name': 'QA老师',
                'gender': 'female',
                'username': 'qa_teacher',
                'avatar': {'face': 2, 'hair': 1},
            }),
            content_type='application/json',
        )
        self.assertEqual(settings.status_code, 200)
        self.assertTrue(settings.json()['ok'])
        teacher = Teacher.objects.get(username='qa_teacher')
        self.assertEqual(teacher.display_name, 'QA老师')
        self.assertEqual(teacher.gender, 'female')

        self.client.get(reverse('teacher_logout'))
        gated = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(gated.status_code, 302)

        wrong = self._login('qa_teacher', 'wrongpass')
        self.assertContains(wrong, '用户名或密码错误')

        good = self._login('qa_teacher', 'secret123')
        self.assertEqual(good.url, reverse('teacher_dashboard'))

    def test_03_create_publish_public_quiz_and_assign_practice(self):
        TeacherInviteCode.objects.create(code='QA2', max_uses=1)
        self.client.post(reverse('teacher_register'), {
            'invite_code': 'QA2',
            'username': 'qa_author',
            'password': 'secret123',
            'password_confirm': 'secret123',
        })

        wizard = self.client.get(reverse('kahoot_new'))
        self.assertContains(wizard, '从公共题库选用')
        self.assertContains(wizard, '手动')
        self.assertContains(wizard, 'Excel')

        public_action = self.client.post(reverse('kahoot_start'), {
            'title': '可忽略',
            'action': 'public',
        })
        self.assertEqual(public_action.url, reverse('kahoot_public_list'))

        created = self.client.post(reverse('kahoot_start'), {
            'title': 'QA公开地理',
            'action': 'manual',
        })
        self.assertEqual(created.status_code, 302)
        quiz = QuizSet.objects.get(title='QA公开地理')
        self.assertEqual(created.url, reverse('kahoot_editor', args=[quiz.pk]))

        editor = self.client.get(reverse('kahoot_editor', args=[quiz.pk]))
        self.assertEqual(editor.status_code, 200)

        add = self.client.post(reverse('kahoot_question_add', args=[quiz.pk]))
        qid = add.json()['question']['id']
        save = self.client.post(reverse('kahoot_question_save', args=[quiz.pk]), {
            'question_id': qid,
            'question_type': 'single',
            'text': '中国的首都是？',
            'option_a': '北京',
            'option_b': '上海',
            'option_c': '广州',
            'option_d': '深圳',
            'correct_option': 'A',
            'time_limit': '20',
        })
        self.assertEqual(save.status_code, 200)
        self.assertEqual(save.json()['question']['text'], '中国的首都是？')

        add2 = self.client.post(reverse('kahoot_question_add', args=[quiz.pk]))
        qid2 = add2.json()['question']['id']
        save2 = self.client.post(reverse('kahoot_question_save', args=[quiz.pk]), {
            'question_id': qid2,
            'question_type': 'judgment',
            'text': '赤道穿过非洲。',
            'option_a': '正确',
            'option_b': '错误',
            'judgment_correct': 'A',
            'time_limit': '15',
        })
        self.assertEqual(save2.status_code, 200)

        add3 = self.client.post(reverse('kahoot_question_add', args=[quiz.pk]))
        qid3 = add3.json()['question']['id']
        save3 = self.client.post(reverse('kahoot_question_save', args=[quiz.pk]), {
            'question_id': qid3,
            'question_type': 'multiple',
            'text': '哪些是直辖市？',
            'option_a': '北京',
            'option_b': '上海',
            'option_c': '杭州',
            'option_d': '重庆',
            'correct_options': ['A', 'B', 'D'],
            'time_limit': '25',
        })
        self.assertEqual(save3.status_code, 200)
        self.assertEqual(Question.objects.get(pk=qid3).question_type, Question.TYPE_MULTIPLE)
        self.assertTrue(Question.objects.get(pk=qid3).is_multiple_choice_correct('A,B,D'))

        add4 = self.client.post(reverse('kahoot_question_add', args=[quiz.pk]))
        qid4 = add4.json()['question']['id']
        save4 = self.client.post(reverse('kahoot_question_save', args=[quiz.pk]), {
            'question_id': qid4,
            'question_type': 'short_answer',
            'text': '中国的首都叫什么？',
            'short_correct': '北京|Beijing',
            'time_limit': '20',
        })
        self.assertEqual(save4.status_code, 200)
        self.assertTrue(Question.objects.get(pk=qid4).is_text_answer_correct('beijing'))

        add5 = self.client.post(reverse('kahoot_question_add', args=[quiz.pk]))
        qid5 = add5.json()['question']['id']
        save5 = self.client.post(reverse('kahoot_question_save', args=[quiz.pk]), {
            'question_id': qid5,
            'question_type': 'word_cloud',
            'text': '用一个词形容中国',
            'time_limit': '30',
        })
        self.assertEqual(save5.status_code, 200)
        self.assertEqual(Question.objects.get(pk=qid5).question_type, Question.TYPE_WORD_CLOUD)

        meta = self.client.post(reverse('kahoot_editor_meta', args=[quiz.pk]), {
            'title': 'QA公开地理',
            'is_public': '1',
        })
        self.assertEqual(meta.status_code, 200)
        self.assertTrue(meta.json()['is_public'])
        self.assertTrue(meta.json()['practice_code'])
        quiz.refresh_from_db()
        code = quiz.practice_code
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isalpha())

        market = self.client.get(reverse('kahoot_public_list'))
        self.assertContains(market, 'QA公开地理')
        self.assertContains(market, code)
        self.assertContains(market, '复制发给学生')

        assign = self.client.get(reverse('practice_assign'))
        self.assertContains(assign, '布置练习')
        self.assertContains(assign, '返回控制台')
        self.assertContains(assign, code)
        self.assertContains(assign, 'data-copy-kind="share"')
        self.assertNotContains(assign, '复制到我的题库')

        preview = self.client.get(
            reverse('kahoot_public_preview', args=[quiz.pk]),
            {'from': 'assign'},
        )
        self.assertContains(preview, '中国的首都是？')
        self.assertContains(preview, '返回布置练习')
        self.assertContains(preview, '复制发给学生')

        search = self.client.get(reverse('practice_assign'), {'q': code})
        self.assertContains(search, 'QA公开地理')

        bank = self.client.get(reverse('question_list'))
        self.assertContains(bank, 'QA公开地理')

        return quiz, code

    def test_04_second_teacher_clones_and_hosts_live_room(self):
        owner = Teacher.objects.create(username='qa_owner', display_name='原作者')
        owner.set_password('secret123')
        owner.save()
        source = QuizSet.objects.create(title='可克隆套题', teacher=owner, is_public=True)
        q = Question.objects.create(
            text='1+1=?',
            question_type=Question.TYPE_SINGLE,
            option_a='1', option_b='2', option_c='3', option_d='4',
            correct_option='B', time_limit=15, teacher=owner, is_public=True,
        )
        from .quiz_set_utils import add_question_to_quiz_set
        add_question_to_quiz_set(source, q)
        ensure_practice_code(source)

        TeacherInviteCode.objects.create(code='QA3', max_uses=1)
        self.client.post(reverse('teacher_register'), {
            'invite_code': 'QA3',
            'username': 'qa_host',
            'password': 'secret123',
            'password_confirm': 'secret123',
        })

        clone = self.client.post(reverse('kahoot_public_clone', args=[source.pk]), {
            'title': '可克隆套题（副本）',
        })
        self.assertEqual(clone.status_code, 302)
        cloned = QuizSet.objects.get(title='可克隆套题（副本）', teacher__username='qa_host')
        self.assertFalse(cloned.is_public)
        self.assertEqual(cloned.question_count(), 1)

        create_page = self.client.get(reverse('room_create'))
        self.assertContains(create_page, '可克隆套题（副本）')
        self.assertContains(create_page, '学生端是否显示题干')

        empty_post = self.client.post(reverse('room_create'), {'name': '空房'})
        self.assertEqual(empty_post.status_code, 200)
        self.assertFalse(Room.objects.filter(name='空房').exists())
        self.assertContains(empty_post, '请选择一套 Kahoot 题目')
        self.assertContains(empty_post, 'join-inline-error')

        launched = self.client.post(reverse('room_create'), {
            'name': 'QA直播课',
            'quiz_set_id': str(cloned.pk),
            'show_question_stem': '1',
        })
        self.assertEqual(launched.status_code, 302)
        room = Room.objects.get(name='QA直播课')
        self.assertEqual(len(room.code), 6)
        self.assertTrue(room.code.isdigit())
        self.assertEqual(room.status, Room.STATUS_WAITING)
        self.assertTrue(room.show_question_stem)
        self.assertEqual(launched.url, reverse('room_host', args=[room.pk]))

        host = self.client.get(reverse('room_host', args=[room.pk]))
        self.assertContains(host, room.code)
        self.assertContains(host, 'QA直播课')

        state = self.client.get(reverse('room_state_api', args=[room.code]))
        self.assertEqual(state.status_code, 200)
        self.assertEqual(state.json()['status'], 'waiting')

        hidden = create_room_from_quiz_set(cloned, Teacher.objects.get(username='qa_host'), name='隐题干', show_question_stem=False)
        self.assertFalse(hidden.show_question_stem)

        join = self.client.post(reverse('join_room'), {
            'code': room.code,
            'nickname': '学生甲',
        })
        self.assertEqual(join.url, reverse('play', args=[room.code]))
        play = self.client.get(join.url)
        self.assertContains(play, '学生甲')
        self.assertContains(play, 'play-word-cloud-wrap')
        self.assertContains(play, 'js/wordcloud.js')
        self.assertNotContains(play, '开始练习')

        ended_room = Room.objects.create(code='111111', name='已结束', status=Room.STATUS_ENDED)
        ended_join = self.client.post(reverse('join_room'), {
            'code': '111111',
            'nickname': '迟到',
        })
        self.assertContains(ended_join, '该房间游戏已结束', status_code=422)

        start_game_for_room(room.code)
        room.refresh_from_db()
        self.assertEqual(room.status, Room.STATUS_PLAYING)
        live = get_room_state(room)
        self.assertIn(live['status'], ('playing', 'waiting'))
        self.assertIn('countdown_remaining_ms', live)

        analytics_page = self.client.get(reverse('room_analytics_page', args=[room.pk]))
        self.assertEqual(analytics_page.status_code, 200)
        analytics_data = self.client.get(reverse('room_analytics_data', args=[room.pk]))
        self.assertEqual(analytics_data.status_code, 200)

    def test_05_practice_mode_score_and_leaderboard(self):
        owner = Teacher.objects.create(username='qa_practice_owner')
        owner.set_password('secret123')
        owner.save()
        quiz = QuizSet.objects.create(title='练习验收套题', teacher=owner, is_public=True)
        q1 = Question.objects.create(
            text='首都？', question_type=Question.TYPE_SINGLE,
            option_a='北京', option_b='上海', option_c='广州', option_d='深圳',
            correct_option='A', time_limit=20, teacher=owner,
        )
        q2 = Question.objects.create(
            text='2+2=?', question_type=Question.TYPE_SINGLE,
            option_a='3', option_b='4', option_c='5', option_d='6',
            correct_option='B', time_limit=15, teacher=owner,
        )
        from .quiz_set_utils import add_question_to_quiz_set
        add_question_to_quiz_set(quiz, q1)
        add_question_to_quiz_set(quiz, q2)
        code = ensure_practice_code(quiz)

        guest = self.client
        join = guest.post(reverse('join_room'), {'code': code.lower(), 'nickname': '练习员'})
        self.assertEqual(join.url, reverse('practice_play', args=[code]))
        lobby = guest.get(join.url)
        self.assertContains(lobby, '开始练习')
        self.assertContains(lobby, '练习验收套题')
        self.assertContains(lobby, '个人练习')
        self.assertNotContains(lobby, '等待老师开始游戏')
        html = lobby.content.decode()
        self.assertLess(html.find('window.PRACTICE_BOOT'), html.find('js/practice.js'))

        start = guest.post(
            reverse('practice_start', args=[code]),
            data=json.dumps({'avatar': {'face': 1, 'hair': 0}}),
            content_type='application/json',
        )
        self.assertTrue(start.json()['ok'])
        token = start.json()['token']
        payload = start.json()['quiz']
        self.assertEqual(len(payload['questions']), 2)
        self.assertNotIn('correct_option', payload['questions'][0])

        right = guest.post(
            reverse('practice_answer', args=[code]),
            data=json.dumps({
                'token': token, 'question_id': q1.id, 'selected': 'A', 'response_time_ms': 800,
            }),
            content_type='application/json',
        )
        self.assertTrue(right.json()['is_correct'])
        self.assertGreater(right.json()['points'], 0)

        wrong = guest.post(
            reverse('practice_answer', args=[code]),
            data=json.dumps({
                'token': token, 'question_id': q2.id, 'selected': 'A', 'response_time_ms': 400,
            }),
            content_type='application/json',
        )
        self.assertFalse(wrong.json()['is_correct'])

        done = guest.post(
            reverse('practice_finish', args=[code]),
            data=json.dumps({'token': token}),
            content_type='application/json',
        )
        self.assertEqual(done.json()['score'], right.json()['points'])
        self.assertEqual(done.json()['leaderboard'][0]['nickname'], '练习员')
        self.assertEqual(PracticeAttempt.objects.filter(quiz_set=quiz, finished_at__isnull=False).count(), 1)
        board = practice_leaderboard(quiz)
        self.assertEqual(board[0]['rank'], 1)

        other = self.client_class()
        other.post(reverse('join_room'), {'code': code, 'nickname': '第二人'})
        start2 = other.post(
            reverse('practice_start', args=[code]),
            data=json.dumps({'avatar': {'face': 0, 'hair': 0}}),
            content_type='application/json',
        )
        token2 = start2.json()['token']
        other.post(
            reverse('practice_answer', args=[code]),
            data=json.dumps({
                'token': token2, 'question_id': q1.id, 'selected': 'B', 'response_time_ms': 900,
            }),
            content_type='application/json',
        )
        other.post(
            reverse('practice_answer', args=[code]),
            data=json.dumps({
                'token': token2, 'question_id': q2.id, 'selected': 'A', 'response_time_ms': 900,
            }),
            content_type='application/json',
        )
        finish2 = other.post(
            reverse('practice_finish', args=[code]),
            data=json.dumps({'token': token2}),
            content_type='application/json',
        )
        self.assertEqual(finish2.json()['leaderboard'][0]['nickname'], '练习员')
        self.assertEqual(len(finish2.json()['leaderboard']), 2)

    def test_06_excel_import_seed_ai_page_and_auth_gates(self):
        teacher = Teacher.objects.create(username='qa_excel')
        teacher.set_password('secret123')
        teacher.save()
        session = self.client.session
        session['teacher_id'] = teacher.pk
        session.save()

        template = self.client.get(reverse('kahoot_import_template'))
        self.assertEqual(template.status_code, 200)
        self.assertIn('spreadsheet', template['Content-Type'])

        xlsx = build_template_xlsx()
        imported = import_quiz_set_from_xlsx(teacher, 'Excel QA 套题', xlsx)
        self.assertGreaterEqual(imported.question_count(), 3)

        import_page = self.client.get(reverse('kahoot_import'))
        self.assertEqual(import_page.status_code, 200)

        ai_page = self.client.get(reverse('kahoot_ai'))
        self.assertEqual(ai_page.status_code, 200)
        self.assertIn('data-turbo="false"', ai_page.content.decode())

        out = StringIO()
        call_command('seed_public_quizzes', stdout=out)
        seeded = QuizSet.objects.filter(is_public=True, teacher__username='kahoot_market')
        self.assertGreaterEqual(seeded.count(), 6)
        self.assertTrue(seeded.exclude(practice_code='').exclude(practice_code__isnull=True).exists())
        market = self.client.get(reverse('kahoot_public_list'))
        self.assertContains(market, '世界地理入门')
        self.assertContains(market, '课堂暖场词云')

        delete = self.client.post(reverse('kahoot_delete', args=[imported.pk]))
        self.assertEqual(delete.status_code, 302)
        self.assertFalse(QuizSet.objects.filter(pk=imported.pk).exists())

        self.client.logout()
        self.client.session.flush()
        anon = self.client_class()
        self.assertEqual(anon.get(reverse('teacher_dashboard')).status_code, 302)
        self.assertEqual(anon.get(reverse('practice_assign')).status_code, 302)
        self.assertEqual(anon.get(reverse('kahoot_public_list')).status_code, 302)
        self.assertEqual(anon.get(reverse('room_create')).status_code, 302)
        self.assertEqual(anon.get(reverse('kahoot_new')).status_code, 302)
        self.assertEqual(anon.get(reverse('question_list')).status_code, 302)
        self.assertEqual(anon.get(reverse('practice_play', args=['ABCDEF'])).status_code, 302)
