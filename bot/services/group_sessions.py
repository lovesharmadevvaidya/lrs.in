"""Group quiz session manager: multiple users compete in same quiz."""
import asyncio
import time
import uuid
import logging

logger = logging.getLogger(__name__)
_group_sessions = {}

class GroupSessionManager:
    @staticmethod
    def create(chat_id: int, quiz_id: str, quiz_payload: dict, host_id: int):
        session_id = str(uuid.uuid4())
        s = {
            'id': session_id,
            'chat_id': chat_id,
            'host_id': host_id,
            'quiz_id': quiz_id,
            'quiz': quiz_payload,
            'current': 0,
            'scores': {},  # user_id -> score
            'answers': {},  # question_index -> {user_id: selected}
            'started_at': time.time(),
            'question_tasks': {},
        }
        _group_sessions[session_id] = s
        return s

    @staticmethod
    def get(session_id: str):
        return _group_sessions.get(session_id)

    @staticmethod
    def answer(session_id: str, question_index: int, user_id: int, selected: int):
        s = _group_sessions.get(session_id)
        if not s:
            return False
        if question_index != s['current']:
            return False
        # ensure user hasn't answered this question
        qmap = s['answers'].setdefault(question_index, {})
        if user_id in qmap:
            return False
        qmap[user_id] = selected
        correct = s['quiz']['questions'][question_index]['correct_index']
        if selected == correct:
            s['scores'][user_id] = s['scores'].get(user_id, 0) + 1
        return True

    @staticmethod
    def timeout(session_id: str, question_index: int):
        s = _group_sessions.get(session_id)
        if not s:
            return
        # finalize question and move on

    @staticmethod
    def next(session_id: str):
        s = _group_sessions.get(session_id)
        if not s:
            return None
        s['current'] += 1
        return s['current']

    @staticmethod
    def finish(session_id: str):
        return _group_sessions.pop(session_id, None)

    @staticmethod
    def schedule_timeout(session_id: str, question_index: int, seconds: int, coro):
        async def _worker():
            try:
                await asyncio.sleep(seconds)
                await coro()
            except asyncio.CancelledError:
                return
        task = asyncio.create_task(_worker())
        s = _group_sessions.get(session_id)
        if s:
            s['question_tasks'][question_index] = task
        return task
