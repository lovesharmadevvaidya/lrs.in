import uuid
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.config import settings
from bot.services.firestore import FirestoreClient

logger = logging.getLogger(__name__)

ADMIN_ONLY_MSG = "You must be an admin to use this command."

async def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_id_list

from bot.utils.helpers import rate_limit

@rate_limit()
async def create_quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id):
        return await update.message.reply_text(ADMIN_ONLY_MSG)
    draft_id = str(user.id)
    draft = {
        'title': '',
        'subject': '',
        'time_per_question': 15,
        'is_premium': False,
        'questions': []
    }
    await FirestoreClient.set_doc('quiz_drafts', draft_id, draft)
    await update.message.reply_text("Draft created. Use /set_quiz_title, /set_subject, /set_time_per_question, /add_question, /add_options, /set_correct_option and /publish_quiz to build it.")

async def set_quiz_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id):
        return await update.message.reply_text(ADMIN_ONLY_MSG)
    title = ' '.join(context.args)
    if not title:
        return await update.message.reply_text("Usage: /set_quiz_title Your Quiz Title (max 300 chars)")
    if len(title) > 300:
        return await update.message.reply_text("Title too long (max 300 chars)")
    draft_id = str(user.id)
    draft = await FirestoreClient.get_doc('quiz_drafts', draft_id) or {}
    draft['title'] = title
    await FirestoreClient.set_doc('quiz_drafts', draft_id, draft)
    await update.message.reply_text("Title set.")

async def set_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id):
        return await update.message.reply_text(ADMIN_ONLY_MSG)
    subject = ' '.join(context.args)
    if not subject:
        return await update.message.reply_text("Usage: /set_subject SubjectName")
    draft_id = str(user.id)
    draft = await FirestoreClient.get_doc('quiz_drafts', draft_id) or {}
    draft['subject'] = subject
    await FirestoreClient.set_doc('quiz_drafts', draft_id, draft)
    await update.message.reply_text("Subject set.")

async def set_time_per_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id):
        return await update.message.reply_text(ADMIN_ONLY_MSG)
    if not context.args or not context.args[0].isdigit():
        return await update.message.reply_text("Usage: /set_time_per_question 15 (seconds)")
    secs = int(context.args[0])
    if secs < 5 or secs > 600:
        return await update.message.reply_text("Time must be between 5 and 600 seconds")
    draft_id = str(user.id)
    draft = await FirestoreClient.get_doc('quiz_drafts', draft_id) or {}
    draft['time_per_question'] = secs
    await FirestoreClient.set_doc('quiz_drafts', draft_id, draft)
    await update.message.reply_text("Time per question set.")

async def add_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id):
        return await update.message.reply_text(ADMIN_ONLY_MSG)
    q_text = ' '.join(context.args)
    if not q_text:
        return await update.message.reply_text("Usage: /add_question Your question text (max 300 chars)")
    if len(q_text) > 300:
        return await update.message.reply_text("Question too long (max 300 chars)")
    draft_id = str(user.id)
    draft = await FirestoreClient.get_doc('quiz_drafts', draft_id) or {'questions': []}
    q = {'question_text': q_text, 'options': [], 'correct_index': None}
    draft.setdefault('questions', []).append(q)
    await FirestoreClient.set_doc('quiz_drafts', draft_id, draft)
    await update.message.reply_text(f"Added question #{len(draft['questions'])-1}")

async def add_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id):
        return await update.message.reply_text(ADMIN_ONLY_MSG)
    if len(context.args) < 5:
        return await update.message.reply_text("Usage: /add_options <question_index> option1 | option2 | option3 | option4 (separate options with | )")
    # args begins with index then the rest joined
    try:
        q_idx = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("Invalid question index")
    rest = ' '.join(context.args[1:])
    parts = [p.strip() for p in rest.split('|') if p.strip()]
    if len(parts) != 4:
        return await update.message.reply_text("You must provide exactly 4 options separated by |")
    draft_id = str(user.id)
    draft = await FirestoreClient.get_doc('quiz_drafts', draft_id) or {}
    questions = draft.setdefault('questions', [])
    if q_idx < 0 or q_idx >= len(questions):
        return await update.message.reply_text("Question index out of range")
    questions[q_idx]['options'] = parts
    await FirestoreClient.set_doc('quiz_drafts', draft_id, draft)
    await update.message.reply_text(f"Options set for question {q_idx}.")

async def set_correct_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id):
        return await update.message.reply_text(ADMIN_ONLY_MSG)
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /set_correct_option <question_index> <0-3>")
    try:
        q_idx = int(context.args[0])
        correct = int(context.args[1])
    except ValueError:
        return await update.message.reply_text("Invalid numbers")
    if correct < 0 or correct > 3:
        return await update.message.reply_text("Correct option must be 0-3")
    draft_id = str(user.id)
    draft = await FirestoreClient.get_doc('quiz_drafts', draft_id) or {}
    questions = draft.setdefault('questions', [])
    if q_idx < 0 or q_idx >= len(questions):
        return await update.message.reply_text("Question index out of range")
    questions[q_idx]['correct_index'] = correct
    await FirestoreClient.set_doc('quiz_drafts', draft_id, draft)
    await update.message.reply_text(f"Correct option set for question {q_idx}.")

async def publish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id):
        return await update.message.reply_text(ADMIN_ONLY_MSG)
    draft_id = str(user.id)
    draft = await FirestoreClient.get_doc('quiz_drafts', draft_id)
    if not draft:
        return await update.message.reply_text("No draft found. Create one with /create_quiz")
    # validate
    required = ['title', 'subject', 'time_per_question']
    for r in required:
        if not draft.get(r):
            return await update.message.reply_text(f"Draft missing {r}. Set it before publishing.")
    if not draft.get('questions'):
        return await update.message.reply_text("Add at least one question before publishing.")
    for idx, q in enumerate(draft['questions']):
        if not q.get('question_text') or not q.get('options') or q.get('correct_index') is None:
            return await update.message.reply_text(f"Question {idx} is incomplete. Ensure text, 4 options and correct option are set.")
    quiz_id = str(uuid.uuid4())
    payload = {
        'title': draft['title'],
        'subject': draft['subject'],
        'time_per_question': draft['time_per_question'],
        'is_premium': draft.get('is_premium', False),
        'questions': draft['questions']
    }
    await FirestoreClient.create_quiz(quiz_id, payload)
    await FirestoreClient.delete_doc('quiz_drafts', draft_id)
    await update.message.reply_text(f"Quiz published with id: {quiz_id}")

async def list_draft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id):
        return await update.message.reply_text(ADMIN_ONLY_MSG)
    draft = await FirestoreClient.get_doc('quiz_drafts', str(user.id))
    if not draft:
        return await update.message.reply_text("No draft found")
    await update.message.reply_text(str(draft))

async def register_quiz_create_handlers(app):
    app.add_handler(CommandHandler('create_quiz', create_quiz_cmd))
    app.add_handler(CommandHandler('set_quiz_title', set_quiz_title))
    app.add_handler(CommandHandler('set_subject', set_subject))
    app.add_handler(CommandHandler('set_time_per_question', set_time_per_question))
    app.add_handler(CommandHandler('add_question', add_question))
    app.add_handler(CommandHandler('add_options', add_options))
    app.add_handler(CommandHandler('set_correct_option', set_correct_option))
    app.add_handler(CommandHandler('publish_quiz', publish_quiz))
    app.add_handler(CommandHandler('list_draft', list_draft))
