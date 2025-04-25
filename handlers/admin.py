from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from db import is_admin, add_category, set_user_limit, find_user_by_id_or_username, get_user_file_stats


def register_admin_handler(bot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(message: Message):
        user_id = message.from_user.id
        if not is_admin(user_id):
            bot.reply_to(message, "⛔ У вас нет доступа к админ-панели.")
            return

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📂 Категории", callback_data="admin_categories"),
            InlineKeyboardButton("👤 Пользователи", callback_data="admin_users"),
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
        )
        bot.send_message(message.chat.id, "🛠 Админ-панель:", reply_markup=markup)

    @bot.message_handler(func=lambda msg: msg.chat.id in bot.temp_admin_step)
    def handle_admin_input(msg: Message):
        chat_id = msg.chat.id
        step = bot.temp_admin_step.get(chat_id)

        if step == 'awaiting_category_name':
            category_name = msg.text.strip()
            add_category(category_name)
            bot.send_message(chat_id, f"✅ Категория «{category_name}» добавлена.")
            del bot.temp_admin_step[chat_id]

        elif step.startswith("set_limit_for_"):
            target_user_id = int(step.split("_")[-1])
            try:
                gb_limit = float(msg.text.strip().replace(',', '.'))  # на случай если юзер введёт 1,5
                if gb_limit < 0:
                    raise ValueError

                byte_limit = int(gb_limit * 1024 * 1024 * 1024) if gb_limit > 0 else None
                set_user_limit(target_user_id, byte_limit)

                bot.send_message(
                    chat_id,
                    f"✅ Лимит для пользователя {target_user_id} установлен: {f'{gb_limit:.2f} ГБ' if byte_limit else 'по умолчанию'}."
                )
                del bot.temp_admin_step[chat_id]

            except ValueError:
                bot.send_message(chat_id, "❌ Введите корректное число. Пример: 1.5 или 0 для сброса.")

        @bot.message_handler(func=lambda msg: msg.chat.id in bot.temp_admin_step)
        def handle_user_admin_input(msg: Message):
            chat_id = msg.chat.id
            step = bot.temp_admin_step.get(chat_id)

            if step == 'awaiting_user_search':
                identifier = msg.text.strip().lstrip('@')
                user = find_user_by_id_or_username(identifier)  # функция в db.py

                if not user:
                    bot.send_message(chat_id, "🙅 Пользователь не найден.")
                    return

                # user = (user_id, username, first_name, is_admin, max_file_size, registered_at)
                file_stats = get_user_file_stats(user[0])  # тоже из db.py

                text = f"""👤 <b>{user[2]}</b> (@{user[1]} / ID: {user[0]})
        🕐 Регистрация: {user[5]}
        📁 Файлов: {file_stats['count']}
        📦 Общий объём: {file_stats['size'] // 1024} KB
        🔒 Приватных: {file_stats['private']} | 🌍 Публичных: {file_stats['public']}
        📐 Лимит: {user[4] if user[4] else 'По умолчанию'} байт
        """

                markup = InlineKeyboardMarkup()
                markup.add(
                    InlineKeyboardButton("✏ Изменить лимит", callback_data=f"edit_limit_{user[0]}"),
                )

                bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)
                del bot.temp_admin_step[chat_id]

