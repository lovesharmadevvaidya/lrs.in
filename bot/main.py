"""Entry point for the Quiz Bot using python-telegram-bot (async)."""
# Ensure the project root is on sys.path so running the script directly still resolves package imports
import os
import sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import asyncio
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder

from bot.config import settings
from bot.handlers.start import register_start_handlers
from bot.handlers.quiz_create import register_quiz_create_handlers
from bot.handlers.quiz_play import register_quiz_play_handlers
from bot.handlers.leaderboard import register_leaderboard_handlers
from bot.handlers.group_quiz import register_group_handlers
from bot.services.firestore import FirestoreClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def main() -> None:
    # Initialize services
    await FirestoreClient.init()

    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).concurrent_updates(True).build()

    # Register handlers
    register_start_handlers(app)
    register_quiz_create_handlers(app)
    register_quiz_play_handlers(app)
    register_leaderboard_handlers(app)
    register_group_handlers(app)

    # global error handler
    async def _error_handler(update, context):
        logger.exception("Unhandled error in update: %s", update)
    app.add_error_handler(_error_handler)

    # Run the bot
    logger.info("Starting bot")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    # Run forever
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
