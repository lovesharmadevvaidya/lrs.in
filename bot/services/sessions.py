"""Session manager for active quizzes.
This is an in-memory manager suitable for single-instance deployments.
For production scale, substitute with Redis or similar.
"""
import asyncio
import time
import uuid
import logging

logger = logging.getLogger(__name__)

_sessions = {}

class SessionError(Exception):
    pass

class SessionManager:
    @staticmethod
    def create_session(user_id: int, quiz_id: str, quiz_payload: dict):
        session_id = str(uuid.uuid4())
        now = time.time()
        s = {
            'id': session_id,
            'user_id': user_id,
            'quiz_id': quiz_id,
            'quiz': quiz_payload,
            'current': 0,
            'score': 0,
            'started_at': now,
            'answers': [],
            'question_tasks': {},  # question_index -> asyncio.Task
            'locked': False,
        }
        _sessions[session_id] = s
        return s

    @staticmethod
    def get(session_id: str):
        return _sessions.get(session_id)

    @staticmethod
    def answer(session_id: str, question_index: int, selected_index: int, time_taken: float):
        s = _sessions.get(session_id)
        if not s:
            raise SessionError("Session not found")
        if question_index != s['current']:
            raise SessionError("Question mismatch or already progressed")
        # ensure not already answered
        if len(s['answers']) > question_index:
            raise SessionError("Already answered")
        q = s['quiz']['questions'][question_index]
        correct = q['correct_index']
        is_correct = (selected_index == correct)
        if is_correct:
            s['score'] += 1
        s['answers'].append({
            'selected': selected_index,
            'correct': correct,
            'is_correct': is_correct,
            'time_taken': time_taken
        })
        # cancel timeout task
        task = s['question_tasks'].pop(question_index, None)
        if task and not task.done():
            task.cancel()
        return is_correct

    @staticmethod
    def timeout(session_id: str, question_index: int):
        s = _sessions.get(session_id)
        if not s:
            return
        # record as unanswered (None)
        s['answers'].append({
            'selected': None,
            'correct': s['quiz']['questions'][question_index]['correct_index'],
            'is_correct': False,
            'time_taken': None
        })
        # proceed to next

    @staticmethod
    def next_question(session_id: str):
        s = _sessions.get(session_id)
        if not s:
            return None
        s['current'] += 1
        return s['current']

    @staticmethod
    def finish(session_id: str):
        s = _sessions.pop(session_id, None)
        return s

    @staticmethod
    def schedule_timeout(session_id: str, question_index: int, seconds: int, coro):
        async def _worker():
            try:
                await asyncio.sleep(seconds)
                await coro()
            except asyncio.CancelledError:
                return
        task = asyncio.create_task(_worker())
        s = _sessions.get(session_id)
        if s:
            s['question_tasks'][question_index] = task
        return task
