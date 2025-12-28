from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("▶️ Play Quiz", callback_data='play_quiz')],
        [InlineKeyboardButton("🏆 My Score", callback_data='my_score'), InlineKeyboardButton("📈 Leaderboard", callback_data='leaderboard')],
        [InlineKeyboardButton("💎 Premium", callback_data='premium'), InlineKeyboardButton("❓ Help", callback_data='help')],
    ]
    return InlineKeyboardMarkup(keyboard)


def subject_selection_keyboard(subjects: List[str]):
    keyboard = [[InlineKeyboardButton(s, callback_data=f'subject:{s}')] for s in subjects]
    return InlineKeyboardMarkup(keyboard)


def options_keyboard(options: List[str], prefix: str = 'answer'):
    keyboard = []
    for idx, opt in enumerate(options):
        label = f"{['A','B','C','D'][idx]} - {opt[:40]}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f'{prefix}:{idx}')])
    return InlineKeyboardMarkup(keyboard)
