from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from bot.utils.keyboards import main_menu_keyboard
from bot.config import settings

from bot.utils.helpers import rate_limit

@rate_limit()
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"Hi {user.first_name}! 🎯\n\n" 
        "Use the buttons below to start a quiz or view your stats."
    )
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())

async def _play_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Choose a subject:", reply_markup=None)

async def _my_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Your scores (coming soon)")

async def _leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Leaderboards (coming soon)")

async def _premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Premium features (coming soon)")

async def _help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Help: Ask admins for guidance.")


def register_start_handlers(app):
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CallbackQueryHandler(_play_callback, pattern='^play_quiz$'))
    app.add_handler(CallbackQueryHandler(_my_score, pattern='^my_score$'))
    app.add_handler(CallbackQueryHandler(_leaderboard, pattern='^leaderboard$'))
    app.add_handler(CallbackQueryHandler(_premium, pattern='^premium$'))
    app.add_handler(CallbackQueryHandler(_help, pattern='^help$'))
