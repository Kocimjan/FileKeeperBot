from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from db import save_file, save_file_tags


def register_file_handler(bot):
    @bot.message_handler(content_types=['document', 'video', 'audio', 'photo'])
    def handle_single_file(message: Message):
        file_info = message.document or message.video or message.audio or message.photo[-1]  # последняя — самое большое качество фото

        file_name = getattr(file_info, 'file_name', 'Без имени')
        file_size = getattr(file_info, 'file_size', 0)
        file_id = file_info.file_id
        mime_type = getattr(file_info, 'mime_type', None)

        # Сохраняем временно в memory для связи с callback
        bot.temp_file_data = {
            message.chat.id: {
                'file_id': file_id,
                'file_name': file_name,
                'file_size': file_size,
                'mime_type': mime_type,
                'message_id': message.message_id,
            }
        }

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🔒 Только мне", callback_data="save_private"),
            InlineKeyboardButton("🌍 Публично", callback_data="save_public")
        )

        bot.send_message(message.chat.id, "Выберите режим сохранения файла:", reply_markup=markup)

        @bot.message_handler(func=lambda message: message.chat.id in bot.temp_file_data)
        def handle_text_step(message: Message):
            chat_id = message.chat.id
            data = bot.temp_file_data.get(chat_id)

            if not data:
                return

            step = data.get('step')

            if step == 'awaiting_description':
                desc = message.text.strip()
                data['description'] = '' if desc == '-' else desc
                data['step'] = 'awaiting_tags'
                bot.send_message(chat_id, "🏷 Введите теги (через запятую или пробел):")

            elif step == 'awaiting_tags':
                tags = [t.strip().lower() for t in message.text.replace(',', ' ').split() if t.strip()]
                data['tags'] = tags

                # Сохраняем файл
                save_file(
                    file_id=data['file_id'],
                    file_name=data['file_name'],
                    file_size=data['file_size'],
                    mime_type=data['mime_type'],
                    uploader_id=message.from_user.id,
                    is_public=data['is_public'],
                    category_id=data['category_id'],
                    description=data.get('description', '')
                )

                # Сохраняем теги
                save_file_tags(data['file_id'], tags)

                bot.send_message(chat_id, "✅ Файл успешно сохранён с описанием и тегами.")
                del bot.temp_file_data[chat_id]

