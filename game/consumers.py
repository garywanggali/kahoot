import json
import uuid

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import Answer, Player, Room
from .utils import calculate_points, get_room_state


def broadcast_room(room_code, event_type, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'room_{room_code}',
        {'type': 'room_message', 'event': event_type, 'data': data},
    )


class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'room_{self.room_code}'

        try:
            self.room = await self.get_room()
        except Room.DoesNotExist:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'join':
            await self.handle_join(data)
        elif action == 'start_game':
            await self.handle_start_game()
        elif action == 'next_question':
            await self.handle_next_question()
        elif action == 'submit_answer':
            await self.handle_submit_answer(data)
        elif action == 'end_question':
            await self.handle_end_question()
        elif action == 'get_state':
            await self.send_state()

    async def room_message(self, event):
        await self.send(text_data=json.dumps({
            'event': event['event'],
            'data': event['data'],
        }))

    async def handle_join(self, data):
        nickname = data.get('nickname', '').strip()
        session_id = data.get('session_id', '')

        if not nickname or len(nickname) > 50:
            await self.send(text_data=json.dumps({
                'event': 'error',
                'data': {'message': '请输入有效昵称'},
            }))
            return

        if not session_id:
            session_id = str(uuid.uuid4())

        player, created = await self.get_or_create_player(nickname, session_id)
        if not created and player.session_id != session_id:
            await self.send(text_data=json.dumps({
                'event': 'error',
                'data': {'message': '该昵称已被使用'},
            }))
            return

        self.session_id = session_id
        self.player_id = player.id

        state = await self.get_room_state_async()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'room_message',
                'event': 'player_joined',
                'data': {
                    'player_count': state['player_count'],
                    'leaderboard': state['leaderboard'],
                },
            },
        )
        await self.send(text_data=json.dumps({
            'event': 'joined',
            'data': {
                'session_id': session_id,
                'player_id': player.id,
                'nickname': player.nickname,
                'state': state,
            },
        }))

    async def handle_start_game(self):
        room = await self.get_room()
        if room.status != Room.STATUS_WAITING:
            return
        questions = await self.get_questions_count()
        if questions == 0:
            return

        await self.update_room(
            status=Room.STATUS_PLAYING,
            current_question_index=0,
            question_started_at=timezone.now(),
        )
        state = await self.get_room_state_async()
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'room_message', 'event': 'game_started', 'data': state},
        )

    async def handle_next_question(self):
        room = await self.get_room()
        questions_count = await self.get_questions_count()

        if room.current_question_index + 1 >= questions_count:
            await self.update_room(status=Room.STATUS_ENDED)
            state = await self.get_room_state_async()
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'room_message', 'event': 'game_ended', 'data': state},
            )
            return

        await self.update_room(
            status=Room.STATUS_PLAYING,
            current_question_index=room.current_question_index + 1,
            question_started_at=timezone.now(),
        )
        state = await self.get_room_state_async()
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'room_message', 'event': 'question_started', 'data': state},
        )

    async def handle_submit_answer(self, data):
        if not hasattr(self, 'player_id'):
            return

        room = await self.get_room()
        if room.status != Room.STATUS_PLAYING:
            return

        question = await self.get_current_question()
        if not question:
            return

        selected = data.get('selected_option', '').upper()
        if selected not in ('A', 'B', 'C', 'D'):
            return

        exists = await self.answer_exists(self.player_id, question.id)
        if exists:
            return

        response_time_ms = data.get('response_time_ms', 0)
        is_correct = selected == question.correct_option
        points = calculate_points(question.time_limit, response_time_ms, is_correct)

        await self.create_answer(
            self.player_id, room.id, question.id,
            selected, is_correct, points, response_time_ms,
        )

        if is_correct:
            await self.add_player_score(self.player_id, points)

        await self.send(text_data=json.dumps({
            'event': 'answer_received',
            'data': {
                'is_correct': is_correct,
                'points': points,
                'selected_option': selected,
            },
        }))

        answer_count = await self.get_answer_count(room.id, question.id)
        player_count = await self.get_player_count(room.id)
        if answer_count >= player_count and player_count > 0:
            await self.handle_end_question()

    async def handle_end_question(self):
        room = await self.get_room()
        if room.status != Room.STATUS_PLAYING:
            return

        await self.update_room(status=Room.STATUS_LEADERBOARD)
        state = await self.get_room_state_async()
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'room_message', 'event': 'question_ended', 'data': state},
        )

    async def send_state(self):
        state = await self.get_room_state_async()
        await self.send(text_data=json.dumps({'event': 'state', 'data': state}))

    @staticmethod
    def _sync_get_room(room_code):
        return Room.objects.get(code=room_code)

    async def get_room(self):
        return await Room.objects.aget(code=self.room_code)

    async def get_or_create_player(self, nickname, session_id):
        room = await self.get_room()
        try:
            player = await Player.objects.aget(room=room, nickname=nickname)
            return player, False
        except Player.DoesNotExist:
            player = await Player.objects.acreate(
                room=room, nickname=nickname, session_id=session_id,
            )
            return player, True

    async def get_questions_count(self):
        room = await self.get_room()
        return await room.room_questions.acount()

    async def get_current_question(self):
        room = await self.get_room()
        questions = [rq.question async for rq in room.room_questions.select_related('question').order_by('order').all()]
        if 0 <= room.current_question_index < len(questions):
            return questions[room.current_question_index]
        return None

    async def update_room(self, **kwargs):
        room = await self.get_room()
        for key, value in kwargs.items():
            setattr(room, key, value)
        await room.asave(update_fields=list(kwargs.keys()))

    async def get_room_state_async(self):
        return await database_sync_to_async(get_room_state_by_code)(self.room_code)

    async def answer_exists(self, player_id, question_id):
        return await Answer.objects.filter(player_id=player_id, question_id=question_id).aexists()

    async def create_answer(self, player_id, room_id, question_id, selected, is_correct, points, response_time_ms):
        await Answer.objects.acreate(
            player_id=player_id,
            room_id=room_id,
            question_id=question_id,
            selected_option=selected,
            is_correct=is_correct,
            points=points,
            response_time_ms=response_time_ms,
        )

    async def add_player_score(self, player_id, points):
        player = await Player.objects.aget(id=player_id)
        player.score += points
        await player.asave(update_fields=['score'])

    async def get_answer_count(self, room_id, question_id):
        return await Answer.objects.filter(room_id=room_id, question_id=question_id).acount()

    async def get_player_count(self, room_id):
        return await Player.objects.filter(room_id=room_id).acount()


def get_room_state_by_code(room_code):
    room = Room.objects.get(code=room_code)
    return get_room_state(room)
