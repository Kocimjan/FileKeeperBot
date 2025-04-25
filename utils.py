from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import get_public_files_paginated, get_file_uploader_name, format_size
from keyboards import explore_nav_keyboard


def send_public_files(bot, chat_id, page=0):
    files = get_public_files_paginated(page)
    if not files:
        bot.send_message(chat_id, "🌍 Публичные файлы не найдены.")
        return

    for f in files:
        uploader = get_file_uploader_name(f['uploader_id'])
        caption = f"""📄 <b>{f['file_name']}</b>
📦 Размер: {format_size(f['file_size'])}
👤 Автор: @{uploader or '—'}"""

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📥 Скачать", callback_data=f"download_{f['id']}"))

        bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup)

    # Кнопки пагинации
    nav = explore_nav_keyboard(page)
    bot.send_message(chat_id, f"📃 Страница {page + 1}", reply_markup=nav)


