"""Configuration loaded from environment variables using pydantic."""
try:
    from pydantic import BaseSettings, AnyHttpUrl
except Exception as e:
    raise ImportError("Missing dependency 'pydantic'. Install dependencies with: pip install -r bot/requirements.txt") from e
from typing import List, Optional

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    ADMIN_IDS: str  # comma separated

    FIREBASE_CREDENTIALS_JSON: Optional[str]
    FIRESTORE_PROJECT_ID: Optional[str]

    RAZORPAY_KEY_ID: Optional[str]
    RAZORPAY_KEY_SECRET: Optional[str]

    WEBHOOK_URL: Optional[AnyHttpUrl]
    ENV: str = "development"

    RATE_LIMIT_PER_MIN: int = 30
    REDIS_URL: Optional[str]

    class Config:
        env_file = ".env"

    @property
    def admin_id_list(self) -> List[int]:
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]

settings = Settings()