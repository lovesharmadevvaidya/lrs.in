"""Payment hooks (placeholder). Supports Razorpay webhook processing and premium unlocking.

This is intentionally minimal and safe: real payment verification must verify signatures.
"""
import logging
from fastapi import FastAPI, Request
from bot.services.firestore import FirestoreClient

logger = logging.getLogger(__name__)
app = FastAPI()

@app.post('/payment/webhook')
async def payment_webhook(request: Request):
    payload = await request.json()
    logger.info("Received payment webhook: %s", payload)
    # TODO: verify signature for Razorpay
    # Expected payload includes user_id and quiz_id or purchase_id
    # For now, accept and unlock premium for user
    data = payload.get('data', {})
    user_id = data.get('user_id')
    if user_id:
        # mark user as premium in a simple users collection
        await FirestoreClient.set_doc('users', str(user_id), {'is_premium': True})
    return {"ok": True}
