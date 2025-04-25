from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards import category_keyboard
from db import (get_categories, delete_category_by_id, get_user_by_id, format_size, get_user_file_stats, is_admin,
                get_file_by_db_id)
from utils import send_public_files


def register_callback_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data in ['save_private', 'save_public'])
    def handle_save_mode(call: CallbackQuery):
        chat_id = call.message.chat.id
        user = call.from_user
        data = bot.temp_file_data.get(chat_id)

        if not data:
            bot.answer_callback_query(call.id, "Нет данных о файле.")
            return

        # Обновляем временные данные
        data['is_public'] = 1 if call.data == 'save_public' else 0

        bot.edit_message_text("📂 Выберите категорию для файла:", chat_id, call.message.message_id,
                              reply_markup=category_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
    def handle_category_selected(call: CallbackQuery):
        chat_id = call.message.chat.id
        data = bot.temp_file_data.get(chat_id)

        if not data:
            bot.answer_callback_query(call.id, "Нет данных о файле.")
            return

        category_id = int(call.data.split("_")[1])
        data['category_id'] = category_id
        data['step'] = 'awaiting_description'

        bot.edit_message_text("📂 Категория выбрана.", chat_id, call.message.message_id)
        bot.send_message(chat_id, "✏️ Введите описание файла (или напишите `-`, чтобы пропустить):")

    @bot.callback_query_handler(func=lambda call: call.data == "admin_categories")
    def show_categories(call: CallbackQuery):
        chat_id = call.message.chat.id
        categories = get_categories()
        markup = InlineKeyboardMarkup(row_width=1)

        if not categories:
            markup.add(InlineKeyboardButton("➕ Добавить категорию", callback_data="add_category"))
            bot.edit_message_text("📂 Категорий пока нет.", chat_id, call.message.message_id, reply_markup=markup)
            return

        for cat_id, name in categories:
            markup.add(InlineKeyboardButton(f"❌ {name}", callback_data=f"del_cat_{cat_id}"))

        markup.add(InlineKeyboardButton("➕ Добавить категорию", callback_data="add_category"))

        bot.edit_message_text("📂 Категории:", chat_id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "add_category")
    def ask_for_category_name(call: CallbackQuery):
        chat_id = call.message.chat.id
        bot.temp_admin_step[chat_id] = 'awaiting_category_name'
        bot.send_message(chat_id, "🆕 Введите название новой категории:")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("del_cat_"))
    def delete_category(call: CallbackQuery):
        cat_id = int(call.data.split("_")[2])
        delete_category_by_id(cat_id)  # создадим в db.py

        bot.answer_callback_query(call.id, "Категория удалена.")
        show_categories(call)  # перерисуем список

    @bot.callback_query_handler(func=lambda call: call.data == "admin_users")
    def ask_for_user_identifier(call: CallbackQuery):
        chat_id = call.message.chat.id
        bot.temp_admin_step[chat_id] = 'awaiting_user_search'
        bot.send_message(chat_id, "🔍 Введите @username или ID пользователя:")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_limit_"))
    def ask_for_limit(call: CallbackQuery):
        user_id = int(call.data.split("_")[2])
        chat_id = call.message.chat.id

        bot.temp_admin_step[chat_id] = f"set_limit_for_{user_id}"
        bot.send_message(chat_id,
                         f"✏ Введите новый лимит (в ГБ) для пользователя ID {user_id}, или 0 чтобы сбросить:")

    @bot.callback_query_handler(func=lambda call: call.data == "user_profile")
    def handle_user_profile(call: CallbackQuery):
        chat_id = call.message.chat.id
        user_id = call.from_user.id

        user = get_user_by_id(user_id)
        stats = get_user_file_stats(user_id)

        text = f"""👤 <b>{user['first_name']}</b> (@{user['username'] or '—'})
    🆔 ID: {user_id}
    📥 Файлов: {stats['count']}
    📦 Объём: {format_size(stats['size'])}
    🔒 Приватных: {stats['private']} | 🌍 Публичных: {stats['public']}
    📐 Лимит: {format_size(user['max_file_size'])}
    """

        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, text, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("explore_page_"))
    def handle_explore_page(call: CallbackQuery):
        page = int(call.data.split("_")[-1])
        bot.answer_callback_query(call.id)
        send_public_files(bot, call.message.chat.id, page)

    @bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
    def open_admin_panel(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Нет доступа.")
            return

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📂 Категории", callback_data="admin_categories"),
            InlineKeyboardButton("👤 Пользователи", callback_data="admin_users"),
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
        )
        bot.edit_message_text("⚙ Админ-панель:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("download_"))
    def handle_file_download(call: CallbackQuery):
        file_db_id = int(call.data.split("_")[1])
        chat_id = call.message.chat.id

        file = get_file_by_db_id(file_db_id)  # новая функция
        if file:
            bot.send_document(chat_id, file['file_id'])
        else:
            bot.send_message(chat_id, "❌ Файл не найден.")

        bot.answer_callback_query(call.id)

