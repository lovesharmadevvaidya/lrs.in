"""Firestore client service wrapper for async operations (sync SDK called in thread executor).

Schema outline (Firestore):
- quizzes (collection)
  - {quiz_id} (doc)
    - title
    - subject
    - time_per_question
    - is_premium
    - questions: array of {question_text, options: [A,B,C,D], correct_index}
- results (collection)
  - {result_id}
    - user_id
    - quiz_id
    - score
    - timestamp
    - time_taken
- leaderboard (collection) derived by queries
"""
import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=5)
_db = None

class FirestoreClient:
    @classmethod
    async def init(cls):
        global _db
        if _db is not None:
            return
        # Initialize SDK in thread pool to avoid blocking
        def _init():
            cred_path = None
            from bot.config import settings
            if settings.FIREBASE_CREDENTIALS_JSON:
                cred_path = settings.FIREBASE_CREDENTIALS_JSON
            if cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': settings.FIRESTORE_PROJECT_ID
                })
            else:
                # Fallback to application default
                firebase_admin.initialize_app()
            return firestore.client()

        _db = await asyncio.get_event_loop().run_in_executor(_executor, _init)
        logger.info("Firestore initialized")

    @staticmethod
    async def create_quiz(quiz_id: str, payload: dict):
        def _task():
            doc_ref = _db.collection('quizzes').document(quiz_id)
            doc_ref.set(payload)
            return True
        return await asyncio.get_event_loop().run_in_executor(_executor, _task)

    @staticmethod
    async def get_quiz(quiz_id: str) -> Optional[dict]:
        def _task():
            doc = _db.collection('quizzes').document(quiz_id).get()
            return doc.to_dict() if doc.exists else None
        return await asyncio.get_event_loop().run_in_executor(_executor, _task)

    @staticmethod
    async def list_quizzes_by_subject(subject: str):
        def _task():
            q = _db.collection('quizzes').where('subject', '==', subject).stream()
            return [doc.to_dict() | {'id': doc.id} for doc in q]
        return await asyncio.get_event_loop().run_in_executor(_executor, _task)

    @staticmethod
    async def save_result(payload: dict):
        def _task():
            doc_ref = _db.collection('results').document()
            doc_ref.set(payload)
            return doc_ref.id
        return await asyncio.get_event_loop().run_in_executor(_executor, _task)

    @staticmethod
    async def set_doc(collection: str, doc_id: str, payload: dict):
        def _task():
            _db.collection(collection).document(doc_id).set(payload)
            return True
        return await asyncio.get_event_loop().run_in_executor(_executor, _task)

    @staticmethod
    async def get_doc(collection: str, doc_id: str) -> Optional[dict]:
        def _task():
            doc = _db.collection(collection).document(doc_id).get()
            return doc.to_dict() if doc.exists else None
        return await asyncio.get_event_loop().run_in_executor(_executor, _task)

    @staticmethod
    async def delete_doc(collection: str, doc_id: str) -> bool:
        def _task():
            _db.collection(collection).document(doc_id).delete()
            return True
        return await asyncio.get_event_loop().run_in_executor(_executor, _task)

    @staticmethod
    async def list_subjects():
        def _task():
            docs = _db.collection('quizzes').select(['subject']).stream()
            subjects = set()
            for d in docs:
                data = d.to_dict() or {}
                if 'subject' in data:
                    subjects.add(data['subject'])
            return sorted(list(subjects))
        return await asyncio.get_event_loop().run_in_executor(_executor, _task)

    @staticmethod
    async def get_results_for_timeframe(start_ts, end_ts, quiz_id: Optional[str] = None):
        def _task():
            col = _db.collection('results')
            q = col.where('timestamp', '>=', start_ts).where('timestamp', '<=', end_ts)
            if quiz_id:
                q = q.where('quiz_id', '==', quiz_id)
            docs = q.stream()
            return [d.to_dict() for d in docs]
        return await asyncio.get_event_loop().run_in_executor(_executor, _task)

    # Additional methods for leaderboards and admin queries will be added as needed
