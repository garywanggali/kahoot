#!/usr/bin/env python3
"""Simulate many players joining and answering in one room."""

import argparse
import asyncio
import json
import os
import sys
import time
import uuid
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kahoot_project.settings')
django.setup()

from game.models import Question, Room, RoomQuestion  # noqa: E402

try:
    import websockets
except ImportError:
    print('Missing dependency: pip install websockets')
    sys.exit(1)


def setup_room(question_count=3):
    questions = list(Question.objects.all()[:question_count])
    if not questions:
        raise RuntimeError('No questions in database. Run: python manage.py load_sample_questions')

    room = Room.objects.create(
        code=Room.generate_code(),
        name='Flood Test Room',
        status=Room.STATUS_WAITING,
    )
    for i, question in enumerate(questions):
        RoomQuestion.objects.create(room=room, question=question, order=i)
    return room


async def wait_for_event(ws, event_name, timeout=20):
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        remaining = deadline - time.perf_counter()
        raw = await asyncio.wait_for(ws.recv(), timeout=max(0.1, remaining))
        msg = json.loads(raw)
        if msg.get('event') == event_name:
            return msg
    raise TimeoutError(f'timed out waiting for {event_name}')


async def submit_answer_only(ws_url, nickname, stats):
    try:
        async with websockets.connect(ws_url, open_timeout=15, close_timeout=5) as ws:
            await ws.send(json.dumps({
                'action': 'join',
                'nickname': nickname,
                'session_id': str(uuid.uuid4()),
            }))
            await wait_for_event(ws, 'joined', timeout=20)
            await ws.send(json.dumps({
                'action': 'submit_answer',
                'selected_option': 'B',
                'response_time_ms': 1500,
            }))
            await wait_for_event(ws, 'answer_received', timeout=20)
            stats.answer_ok += 1
    except Exception as exc:
        stats.failures.append(f'{nickname} answer: {type(exc).__name__}: {exc}')


async def run_player(ws_url, nickname, stats, submit_answer=True):
    t0 = time.perf_counter()
    try:
        async with websockets.connect(ws_url, open_timeout=15, close_timeout=5) as ws:
            await ws.send(json.dumps({
                'action': 'join',
                'nickname': nickname,
                'session_id': str(uuid.uuid4()),
            }))
            joined = await wait_for_event(ws, 'joined', timeout=20)
            stats.join_ok += 1
            stats.join_ms.append((time.perf_counter() - t0) * 1000)

            if not submit_answer:
                return

            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=120)
                msg = json.loads(raw)
                event = msg.get('event')
                if event in ('game_started', 'question_started'):
                    break
                if event == 'error':
                    raise RuntimeError(msg['data'].get('message', 'unknown error'))

            await ws.send(json.dumps({
                'action': 'submit_answer',
                'selected_option': 'A',
                'response_time_ms': 1500,
            }))
            answer = await wait_for_event(ws, 'answer_received', timeout=20)
            if answer['data'].get('is_correct') is not None:
                stats.answer_ok += 1
                stats.answer_ms.append((time.perf_counter() - t0) * 1000)
    except Exception as exc:
        stats.failures.append(f'{nickname}: {type(exc).__name__}: {exc}')


async def run_host(ws_url, stats):
    try:
        async with websockets.connect(ws_url, open_timeout=15, close_timeout=5) as ws:
            await asyncio.sleep(0.5)
            await ws.send(json.dumps({'action': 'start_game'}))
            await wait_for_event(ws, 'game_started', timeout=30)
            stats.host_started = True
    except Exception as exc:
        stats.failures.append(f'host: {exc}')


class Stats:
    def __init__(self):
        self.join_ok = 0
        self.answer_ok = 0
        self.host_started = False
        self.join_ms = []
        self.answer_ms = []
        self.failures = []


def percentile(values, pct):
    if not values:
        return 0
    ordered = sorted(values)
    idx = int(len(ordered) * pct / 100)
    idx = min(idx, len(ordered) - 1)
    return ordered[idx]


async def run_flood(room, args):
    ws_url = f'ws://{args.host}:{args.port}/ws/room/{room.code}/'
    stats = Stats()

    print(f'Room: {room.code} | Players: {args.players} | URL: {ws_url}')
    print('Phase 1: concurrent joins...')

    t_start = time.perf_counter()
    player_tasks = [
        asyncio.create_task(run_player(ws_url, f'player{i:03d}', stats, submit_answer=False))
        for i in range(1, args.players + 1)
    ]
    await asyncio.gather(*player_tasks)
    join_elapsed = time.perf_counter() - t_start
    print(f'Phase 1 done in {join_elapsed:.2f}s — joined {stats.join_ok}/{args.players}')

    if args.join_only:
        return stats, 0 if stats.join_ok == args.players else 1

    print('Phase 2: host starts game...')
    host_stats = Stats()
    await run_host(ws_url, host_stats)
    stats.host_started = host_stats.host_started
    if not stats.host_started:
        stats.failures.extend(host_stats.failures)

    print('Phase 3: players submit answers...')
    answer_tasks = []
    for i in range(1, args.players + 1):
        answer_tasks.append(asyncio.create_task(
            submit_answer_only(ws_url, f'player{i:03d}', stats)
        ))
    await asyncio.gather(*answer_tasks)
    elapsed = time.perf_counter() - t_start

    print('\n=== Flood Test Results ===')
    print(f'Room code:        {room.code}')
    print(f'Players joined:   {stats.join_ok}/{args.players}')
    if not args.join_only:
        print(f'Host started:     {stats.host_started}')
        print(f'Answers received: {stats.answer_ok}/{args.players}')
    print(f'Total time:       {elapsed:.2f}s')
    if stats.join_ms:
        print(f'Join latency p50: {percentile(stats.join_ms, 50):.0f}ms')
        print(f'Join latency p95: {percentile(stats.join_ms, 95):.0f}ms')
        print(f'Join latency max: {max(stats.join_ms):.0f}ms')
    if stats.answer_ms:
        print(f'Answer path p50:  {percentile(stats.answer_ms, 50):.0f}ms')
        print(f'Answer path p95:  {percentile(stats.answer_ms, 95):.0f}ms')
    print(f'Failures:         {len(stats.failures)}')
    for err in stats.failures[:15]:
        print(f'  - {err}')
    if len(stats.failures) > 15:
        print(f'  ... and {len(stats.failures) - 15} more')

    ok = stats.join_ok == args.players and (args.join_only or (stats.host_started and stats.answer_ok == args.players))
    return stats, 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description='Flood test for Kahoot room WebSockets')
    parser.add_argument('--players', type=int, default=300)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--room', help='Existing room code (optional)')
    parser.add_argument('--join-only', action='store_true', help='Only test concurrent joins')
    args = parser.parse_args()

    if args.room:
        room = Room.objects.get(code=args.room)
    else:
        room = setup_room()

    stats, code = asyncio.run(run_flood(room, args))
    room.refresh_from_db()
    print(f'DB player count:  {room.players.count()}')
    sys.exit(code)


if __name__ == '__main__':
    main()
