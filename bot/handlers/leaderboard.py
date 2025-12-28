import time
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.services.firestore import FirestoreClient

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /leaderboard [daily|weekly|quiz <quiz_id>]
    args = context.args
    now = int(time.time())
    if not args or args[0] == 'daily':
        start = int((datetime.utcnow() - timedelta(days=1)).timestamp())
        end = now
    elif args[0] == 'weekly':
        start = int((datetime.utcnow() - timedelta(days=7)).timestamp())
        end = now
    elif args[0] == 'quiz' and len(args) == 2:
        start = 0
        end = now
        quiz_id = args[1]
    else:
        return await update.message.reply_text("Usage: /leaderboard [daily|weekly|quiz <quiz_id>]")

    if args and args[0] == 'quiz' and len(args) == 2:
        results = await FirestoreClient.get_results_for_timeframe(start, end, quiz_id=args[1])
    else:
        results = await FirestoreClient.get_results_for_timeframe(start, end)

    # aggregate by user_id -> best score (or highest score, then lower time)
    agg = {}
    for r in results:
        uid = r.get('user_id')
        if uid is None:
            continue
        score = r.get('score', 0)
        t = r.get('time_taken', 0) or 0
        prev = agg.get(uid)
        if not prev or (score > prev['score'] or (score == prev['score'] and t < prev['time'])):
            agg[uid] = {'score': score, 'time': t}
    if not agg:
        return await update.message.reply_text("No results for the period.")
    items = sorted(agg.items(), key=lambda x: (-x[1]['score'], x[1]['time']))[:10]
    lines = [f"#{i+1} - {uid}: {v['score']} pts, {v['time']}s" for i, (uid, v) in enumerate(items)]
    await update.message.reply_text("\n".join(lines))


def register_leaderboard_handlers(app):
    app.add_handler(CommandHandler('leaderboard', leaderboard_command))
