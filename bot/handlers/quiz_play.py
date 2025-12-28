import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from bot.services.firestore import FirestoreClient
from bot.services.sessions import SessionManager
from bot.utils.keyboards import subject_selection_keyboard, options_keyboard

logger = logging.getLogger(__name__)

async def show_subjects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # callback 'play_quiz'
    query = update.callback_query
    await query.answer()
    subjects = await FirestoreClient.list_subjects()
    if not subjects:
        return await query.edit_message_text("No quizzes available yet.")
    await query.edit_message_text("Choose a subject:", reply_markup=subject_selection_keyboard(subjects))

async def subject_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # subject:name
    _, subject = data.split(':', 1)
    quizzes = await FirestoreClient.list_quizzes_by_subject(subject)
    if not quizzes:
        return await query.edit_message_text("No quizzes in this subject.")
    keyboard = [[InlineKeyboardButton(q['title'], callback_data=f"quiz:{q['id']}")] for q in quizzes]
    await query.edit_message_text(f"Quizzes for {subject}:", reply_markup=InlineKeyboardMarkup(keyboard))

async def quiz_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, quiz_id = query.data.split(':',1)
    quiz = await FirestoreClient.get_quiz(quiz_id)
    if not quiz:
        return await query.edit_message_text("Quiz not found")
    text = f"*{quiz['title']}*\nSubject: {quiz['subject']}\nQuestions: {len(quiz['questions'])}\nTime per question: {quiz['time_per_question']}s"
    keyboard = [[InlineKeyboardButton("Start Quiz ▶️", callback_data=f"start:{quiz_id}")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    _, quiz_id = query.data.split(':',1)
    quiz = await FirestoreClient.get_quiz(quiz_id)
    if not quiz:
        return await query.edit_message_text("Quiz not found")
    session = SessionManager.create_session(user.id, quiz_id, quiz)
    await send_question(query.message.chat_id, context, session)

async def send_question(chat_id: int, context: ContextTypes.DEFAULT_TYPE, session: dict):
    idx = session['current']
    quiz = session['quiz']
    if idx >= len(quiz['questions']):
        # finish
        s = SessionManager.finish(session['id'])
        total = s['score']
        count = len(s['answers'])
        acc = (total / count * 100) if count else 0
        await context.bot.send_message(chat_id=chat_id, text=f"Quiz finished! Score: {total}/{count} (Accuracy: {acc:.1f}%)")
        # persist result
        payload = {
            'user_id': s['user_id'],
            'quiz_id': s['quiz_id'],
            'score': s['score'],
            'timestamp': int(time.time()),
            'time_taken': int(time.time() - s['started_at'])
        }
        await FirestoreClient.save_result(payload)
        return
    q = quiz['questions'][idx]
    text = f"Q{idx+1}. {q['question_text']}"
    keyboard = options_keyboard(q['options'], prefix=f"ans:{session['id']}:{idx}")
    msg = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)

    # schedule timeout
    async def _timeout():
        try:
            # mark timeout in session
            SessionManager.timeout(session['id'], idx)
            await context.bot.send_message(chat_id=chat_id, text=f"Time's up for question {idx+1} ⏰")
            SessionManager.next_question(session['id'])
            # send next question
            s = SessionManager.get(session['id'])
            if s:
                await send_question(chat_id, context, s)
        except Exception as e:
            logger.exception("Timeout handler error: %s", e)

    SessionManager.schedule_timeout(session['id'], idx, quiz['time_per_question'], _timeout)

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # ans:session_id:idx:sel
    parts = data.split(':')
    if len(parts) != 4:
        return
    _, session_id, q_idx_s, sel_s = parts
    q_idx = int(q_idx_s)
    selected = int(sel_s)
    s = SessionManager.get(session_id)
    if not s:
        return await query.edit_message_text("Session expired or invalid.")
    user = update.effective_user
    if user.id != s['user_id']:
        return await query.answer("This quiz is for another user", show_alert=True)
    # compute time taken as naive
    # Here, we simply mark as answered and give instant feedback
    try:
        is_correct = SessionManager.answer(session_id, q_idx, selected, 0)
    except Exception as e:
        return await query.answer(str(e), show_alert=True)
    emoji = "✅" if is_correct else "❌"
    correct_idx = s['quiz']['questions'][q_idx]['correct_index']
    correct_label = ['A','B','C','D'][correct_idx]
    await query.edit_message_text(f"{emoji} {query.message.text}\n\nCorrect: {correct_label}")
    # proceed to next question
    SessionManager.next_question(session_id)
    s2 = SessionManager.get(session_id)
    if s2:
        await send_question(query.message.chat_id, context, s2)


def register_quiz_play_handlers(app):
    # play flow
    app.add_handler(CallbackQueryHandler(show_subjects, pattern='^play_quiz$'))
    app.add_handler(CallbackQueryHandler(subject_selected, pattern='^subject:'))
    app.add_handler(CallbackQueryHandler(quiz_selected, pattern='^quiz:'))
    app.add_handler(CallbackQueryHandler(start_quiz, pattern='^start:'))
    # answer pattern: ans:session_id:question_index:selected_index
    app.add_handler(CallbackQueryHandler(answer_handler, pattern='^ans:'))
