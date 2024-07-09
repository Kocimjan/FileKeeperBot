import os
import telebot
from telebot import types
import sqlite3

# Получение токена из переменных окружения
# API_TOKEN = '7099691244:AAHr-WegTkGc1gka9GRZOFtSAxk32uv3SgI'
API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')
if not API_TOKEN:
    raise ValueError("No API token provided. Please set the TELEGRAM_BOT_API_TOKEN environment variable.")

AID = []

bot = telebot.TeleBot(API_TOKEN)

# Подключение к базе данных
conn = sqlite3.connect('study_materials.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы для хранения материалов
cursor.execute('''
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        user_id INTEGER
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER,
        file_id TEXT,
        FOREIGN KEY (material_id) REFERENCES materials(id)
    )
''')
conn.commit()


# Словарь для хранения временных данных пользователя
user_data = {}


# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id in AID:
        bot.reply_to(message, "Привет! Я бот для хранения файлов. Используй /add для добавления нового материала, "
                              "/list для просмотра всех материалов, и /search для поиска материалов.")
    else:
        bot.reply_to(message,
                     "Привет! Я бот для хранения учебных материалов. Используй /list для просмотра всех материалов, "
                     "и /search для поиска материалов.")


# Добавление нового материала
@bot.message_handler(commands=['add'])
def add_material(message):
    chat_id = message.chat.id
    if chat_id in AID:
        user_data[chat_id] = {}
        msg = bot.reply_to(message, "Введите название материала:")
        bot.register_next_step_handler(msg, process_title_step)


def process_title_step(message):
    chat_id = message.chat.id
    user_data[chat_id]['title'] = message.text
    msg = bot.reply_to(message, "Введите описание материала:")
    bot.register_next_step_handler(msg, process_description_step)


def process_description_step(message):
    chat_id = message.chat.id
    user_data[chat_id]['description'] = message.text
    msg = bot.reply_to(message, "Отправьте файлы материала (отправьте все файлы, затем напишите /done):")
    bot.register_next_step_handler(msg, process_files_step)


def process_files_step(message):
    chat_id = message.chat.id
    if message.text == '/done':
        cursor.execute("INSERT INTO materials (title, description, user_id) VALUES (?, ?, ?)",
                       (user_data[chat_id]['title'], user_data[chat_id]['description'], chat_id))
        material_id = cursor.lastrowid

        for file_id in user_data[chat_id]['files']:
            cursor.execute("INSERT INTO files (material_id, file_id) VALUES (?, ?)", (material_id, file_id))

        conn.commit()
        bot.reply_to(message, "Материал успешно добавлен!")
        user_data.pop(chat_id)
    elif message.content_type == 'document':
        if 'files' not in user_data[chat_id]:
            user_data[chat_id]['files'] = []
        user_data[chat_id]['files'].append(message.document.file_id)
        msg = bot.reply_to(message, "Файл добавлен. Отправьте следующий файл или напишите /done, чтобы завершить.")
        bot.register_next_step_handler(msg, process_files_step)
    else:
        msg = bot.reply_to(message, "Пожалуйста, отправьте документ или напишите /done, чтобы завершить.")
        bot.register_next_step_handler(msg, process_files_step)


# Пагинация для списка материалов
def generate_materials_markup(page=0, page_size=8):
    cursor.execute("SELECT id, title FROM materials LIMIT ? OFFSET ?", (page_size, page * page_size))
    materials = cursor.fetchall()

    markup = types.InlineKeyboardMarkup()
    for material in materials:
        markup.add(types.InlineKeyboardButton(text=material[1], callback_data=f"view_{material[0]}"))

    if page > 0:
        markup.add(types.InlineKeyboardButton(text="Назад", callback_data=f"page_{page - 1}"))

    if len(materials) == page_size:
        markup.add(types.InlineKeyboardButton(text="Вперед", callback_data=f"page_{page + 1}"))

    return markup


# Просмотр всех материалов
@bot.message_handler(commands=['list'])
def list_materials(message):
    markup = generate_materials_markup()
    bot.send_message(message.chat.id, "Доступные материалы:", reply_markup=markup)


# Обработка инлайн-кнопок
@bot.callback_query_handler(func=lambda call: call.data.startswith('page_'))
def handle_pagination(call):
    page = int(call.data.split('_')[1])
    markup = generate_materials_markup(page)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Учебные материалы:",
                          reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('view_'))
def handle_view_material(call):
    material_id = int(call.data.split('_')[1])
    cursor.execute("SELECT title, description FROM materials WHERE id=?", (material_id,))
    material = cursor.fetchone()
    if material:
        title, description = material
        bot.send_message(call.message.chat.id, f"Название: {title}\nОписание: {description}")

        cursor.execute("SELECT file_id FROM files WHERE material_id=?", (material_id,))
        files = cursor.fetchall()
        for file_id in files:
            bot.send_document(call.message.chat.id, file_id[0])
    else:
        bot.send_message(call.message.chat.id, "Материал не найден.")


# Поиск материалов
@bot.message_handler(commands=['search'])
def search_materials(message):
    msg = bot.reply_to(message, "Введите ключевое слово для поиска:")
    bot.register_next_step_handler(msg, process_search_step)


def process_search_step(message):
    keyword = message.text
    cursor.execute("SELECT id, title, description FROM materials WHERE title LIKE ? OR description LIKE ?",
                   ('%' + keyword + '%', '%' + keyword + '%'))
    materials = cursor.fetchall()
    if materials:
        for material in materials:
            title, description = material[1], material[2]
            bot.send_message(message.chat.id, f"Название: {title}\nОписание: {description}")

            cursor.execute("SELECT file_id FROM files WHERE material_id=?", (material[0],))
            files = cursor.fetchall()
            for file_id in files:
                bot.send_document(message.chat.id, file_id[0])
    else:
        bot.reply_to(message, "Ничего не найдено по вашему запросу.")


bot.infinity_polling()
