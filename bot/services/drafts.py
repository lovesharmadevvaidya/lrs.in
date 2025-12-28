"""Service to manage in-progress quiz drafts for admins."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from bot.services.firestore import FirestoreClient

logger = logging.getLogger(__name__)

class DraftService:
    collection = 'quiz_drafts'

    @staticmethod
    async def create_or_update_draft(admin_id: int, payload: dict):
        # Store drafts under doc id = admin_id
        doc_id = str(admin_id)
        client = FirestoreClient
        # read existing doc and merge
        existing = await client.get_doc('quiz_drafts', doc_id)
        merged = {**(existing or {}), **payload}
        await client.set_doc('quiz_drafts', doc_id, merged)
        return merged

    @staticmethod
    async def get_draft(admin_id: int):
        doc_id = str(admin_id)
        return await FirestoreClient.get_doc('quiz_drafts', doc_id)

    @staticmethod
    async def delete_draft(admin_id: int):
        doc_id = str(admin_id)
        return await FirestoreClient.delete_doc('quiz_drafts', doc_id)
