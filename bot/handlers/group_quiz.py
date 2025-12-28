import logging
import time
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
except Exception as e:
    raise ImportError("python-telegram-bot is not installed or is an incompatible package. Ensure you have installed 'python-telegram-bot[aio]==20.6' and there is no conflicting 'telegram' package installed.") from e
from bot.services.firestore import FirestoreClient
from bot.services.group_sessions import GroupSessionManager

logger = logging.getLogger(__name__)

async def startquiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Command must be used in a group by admin
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == 'private':
        return await update.message.reply_text("Use this command in a group chat where the quiz should run.")
    if not context.args:
        return await update.message.reply_text("Usage: /startquiz <quiz_id>")
    quiz_id = context.args[0]
    quiz = await FirestoreClient.get_quiz(quiz_id)
    if not quiz:
        return await update.message.reply_text("Quiz not found")
    s = GroupSessionManager.create(chat.id, quiz_id, quiz, user.id)
    # post first question
    await post_question(s, context)
    await update.message.reply_text(f"Group quiz started with session id {s['id']}")

async def post_question(session: dict, context: ContextTypes.DEFAULT_TYPE):
    idx = session['current']
    quiz = session['quiz']
    if idx >= len(quiz['questions']):
        # finish
        s = GroupSessionManager.finish(session['id'])
        if not s:
            return
        # prepare leaderboard
        scores = s['scores']
        lines = [f"{i+1}. {uid} - {score}" for i, (uid, score) in enumerate(sorted(scores.items(), key=lambda x: -x[1]))]
        text = "Group Quiz finished!\n" + ("\n".join(lines) if lines else "No one scored points.")
        await context.bot.send_message(chat_id=s['chat_id'], text=text)
        # persist results per user
        for uid, score in scores.items():
            await FirestoreClient.save_result({'user_id': uid, 'quiz_id': s['quiz_id'], 'score': score, 'timestamp': int(time.time()), 'time_taken': 0})
        return
    q = quiz['questions'][idx]
    text = f"Q{idx+1}. {q['question_text']}"
    keyboard = [[InlineKeyboardButton(f"{['A','B','C','D'][i]}", callback_data=f"gans:{session['id']}:{idx}:{i}")] for i in range(len(q['options']))]
    await context.bot.send_message(chat_id=session['chat_id'], text=text, reply_markup=InlineKeyboardMarkup(keyboard))

    async def _timeout():
        GroupSessionManager.timeout(session['id'], idx)
        GroupSessionManager.next(session['id'])
        s2 = GroupSessionManager.get(session['id'])
        if s2:
            await post_question(s2, context)

    GroupSessionManager.schedule_timeout(session['id'], idx, quiz['time_per_question'], _timeout)

async def group_answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(':')
    if len(parts) != 4:
        return
    _, session_id, q_idx_s, sel_s = parts
    q_idx = int(q_idx_s)
    sel = int(sel_s)
    user = update.effective_user
    ok = GroupSessionManager.answer(session_id, q_idx, user.id, sel)
    if not ok:
        return await query.answer("Not accepted (maybe you already answered or session ended)", show_alert=True)
    await query.message.reply_text(f"{user.first_name} answered")

    # we do not progress until timeout; optional: end early if everyone answered


def register_group_handlers(app):
    app.add_handler(CommandHandler('startquiz', startquiz_cmd))
    app.add_handler(CallbackQueryHandler(group_answer_handler, pattern='^gans:'))
