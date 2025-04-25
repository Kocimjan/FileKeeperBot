from telebot.types import Message
from db import create_user, is_admin
from keyboards import main_menu_keyboard


def register_start_handler(bot):
    @bot.message_handler(commands=['start'])
    def start_handler(message: Message):
        user = message.from_user
        create_user(user.id, user.username, user.first_name)

        admin_flag = is_admin(user.id)
        bot.send_message(
            message.chat.id,
            f"👋 Привет, {user.first_name}!\nДобро пожаловать в FileCloud — твое облако в Telegram.",
            reply_markup=main_menu_keyboard(admin_flag)
        )