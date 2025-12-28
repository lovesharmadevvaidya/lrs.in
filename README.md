# Telegram Quiz Bot (Python)

A production-ready Telegram Quiz Maker Bot using python-telegram-bot (async) and Firebase Firestore.

Features:
- Admins can create quizzes via simple commands
- Users can play quizzes one question at a time with timers and inline buttons
- Auto scoring, result storage and leaderboards (daily/weekly/quiz-wise)
- Group quiz mode (skeleton) and payment webhook placeholders
- Rate limiting and basic error handling

Tech Stack:
- Python 3.10+
- python-telegram-bot (async)
- Firebase Firestore
- FastAPI for webhook endpoints (payments)

Quickstart:
1. Create and activate a virtual environment, then copy `.env` and fill values:
   - python -m venv .venv
   - source .venv/bin/activate
   - cp bot/.env.example .env
   - Fill TELEGRAM_BOT_TOKEN, ADMIN_IDS, FIREBASE_CREDENTIALS_JSON, FIRESTORE_PROJECT_ID, etc.
2. Install dependencies: `pip install -r bot/requirements.txt`.
3. Run Firestore init (ensure `FIREBASE_CREDENTIALS_JSON` points to service account JSON)
4. Start the bot (recommended): `python -m bot.main`
   - You can also run `python bot/main.py`, but using `-m` ensures Python's module search path includes the project root and avoids `ModuleNotFoundError: No module named 'bot'`.
5. (Optional) start webhook server: `python -m bot.server` or `python bot/server.py`

If you see an ImportError for missing packages (e.g., `ModuleNotFoundError: No module named 'pydantic'`), install requirements with:

pip install -r bot/requirements.txt

and ensure the venv is activated (`source .venv/bin/activate`).

Deployment
- This can be hosted on Railway, Render or any VPS. Use a process manager (systemd, pm2, or Procfile) and ensure env vars are set.
- For production timers and multi-instance scaling, use Redis for session management and scheduling.

Security & Payments
- Payment webhook endpoint is a placeholder and must verify signatures from Razorpay before unlocking premium features.

See `/bot` for detailed code and handlers.

Troubleshooting: If you see an ImportError like "cannot import name 'InlineKeyboardButton' from 'telegram'", it usually means a conflicting package named `telegram` is installed instead of `python-telegram-bot`.

Solve it by running:

- pip uninstall telegram
- pip install "python-telegram-bot[aio]==20.6"

Then restart the bot.
