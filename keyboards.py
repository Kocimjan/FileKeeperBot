from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import get_categories


def category_keyboard():
    markup = InlineKeyboardMarkup()
    for cat_id, name in get_categories():
        markup.add(InlineKeyboardButton(name, callback_data=f"cat_{cat_id}"))
    return markup


def profile_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📄 Мой профиль", callback_data="user_profile"))
    return markup


def explore_nav_keyboard(page):
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅ Назад", callback_data=f"explore_page_{page - 1}"))
    buttons.append(InlineKeyboardButton("➡ Вперёд", callback_data=f"explore_page_{page + 1}"))
    markup.add(*buttons)
    return markup


def main_menu_keyboard(is_admin=False):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📤 Загрузить файл", switch_inline_query_current_chat=""),
        InlineKeyboardButton("🌍 Публичные файлы", callback_data="explore_page_0"),
        InlineKeyboardButton("📄 Мой профиль", callback_data="user_profile")
    )

    if is_admin:
        markup.add(InlineKeyboardButton("⚙ Админ-панель", callback_data="admin_panel"))

    return markup
