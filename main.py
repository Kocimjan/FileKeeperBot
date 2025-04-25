import telebot
from config import TOKEN
from handlers import commands, files, callbacks, admin

bot = telebot.TeleBot(TOKEN)

# Временное хранилище для FSM-подобных шагов
bot.temp_file_data = {}
bot.temp_admin_step = {}
bot.media_group_buffer = {}

commands.register_start_handler(bot)
files.register_file_handler(bot)
callbacks.register_callback_handlers(bot)
admin.register_admin_handler(bot)

if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling()
