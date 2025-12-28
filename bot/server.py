"""Small FastAPI server to receive webhooks (payments) and health-checks."""
import logging
import uvicorn
from fastapi import FastAPI
from bot.services.payment import app as payment_app

logger = logging.getLogger(__name__)
app = FastAPI()

app.mount('/payment', payment_app)

@app.get('/health')
async def health():
    return {"status":"ok"}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
