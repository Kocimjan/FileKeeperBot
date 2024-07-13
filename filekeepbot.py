import os
import telebot
from telebot import types
import sqlite3
from db import database

# Получение токена из переменных окружения
API_TOKEN = '7067345974:AAHaEPsA9UOiPYMzFTPH3WF1sAQfb8heggc'
if not API_TOKEN:
    raise ValueError("No API token provided. Please set the TELEGRAM_BOT_API_TOKEN environment variable.")

bot = telebot.TeleBot(API_TOKEN)
AID = [906893530, 6690844057]

# Словарь для хранения временных данных пользователя
user_data = {}
db = database('materials.db')

# Подключение к базе данных
conn = sqlite3.connect('materials.db', check_same_thread=False)
cursor = conn.cursor()


def get_categories() -> list:
    if (categories := [category[0] for category in db.execute("SELECT DISTINCT name FROM categories")]):
        return categories


def categories_catalogue(categories):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for category in categories:
        button_text = category
        markup.add(types.InlineKeyboardButton(button_text, callback_data=button_text + '_ctg'))
    markup.add(types.InlineKeyboardButton('Отмена', callback_data='cancel'))
    markup.add(types.InlineKeyboardButton('Доб. Категорию', callback_data='add_ctg'))
    return markup



# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    username = message.from_user.username
    if not db.execute("SELECT * FROM users WHERE tg_id =?", chat_id):
        db.execute("INSERT INTO users (tg_id, username) VALUES (?, ?)", chat_id, username)
        db.commit()
    if chat_id in AID:
        bot.reply_to(message, "Привет! Я бот для хранения файлов. Используй /add для добавления нового материала, "
                              "/list для просмотра всех материалов, и /search для поиска материалов.")
    else:
        bot.reply_to(message, "Привет! Я бот для хранения учебных материалов. Используй /list для просмотра всех "
                              "материалов,"
                              "и /search для поиска материалов.")


# Добавление нового материала
@bot.message_handler(commands=['add'])
def choose_categories(message):
    chat_id = message.chat.id
    if chat_id in AID:
        user_data[chat_id] = {}
        markup = categories_catalogue(get_categories())
        bot.reply_to(message, 'Выберите категорию для материала:', reply_markup=markup)
    else:
        bot.reply_to(message, "Это функция для админов червь блять")


def add_material(message):
    chat_id = message.chat.id
    if chat_id in AID:
        user_data[chat_id] = {'files': []}
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
    msg = bot.reply_to(message, "Отправь файлы материала (до 10 файлов одновременно):")
    bot.register_next_step_handler(msg, process_files_step)


def process_files_step(message):
    chat_id = message.chat.id
    if message.content_type == 'document':
        user_data[chat_id]['files'].append(types.InputMediaDocument(message.document.file_id))
        msg = bot.reply_to(message,
                           "Файл добавлен. Отправьте следующий файл (до 10 файлов) или напишите /done, чтобы завершить.")
        bot.register_next_step_handler(msg, process_files_step)
    elif message.text == '/done':
        if not user_data[chat_id]['files']:
            msg = bot.reply_to(message,
                               "Вы не добавили ни одного файла. Пожалуйста, добавьте файлы и завершите командой /done.")
            bot.register_next_step_handler(msg, process_files_step)

        cursor.execute("INSERT INTO materials (title, description, user_id) VALUES (?, ?, ?)",
                       (user_data[chat_id]['title'], user_data[chat_id]['description'], chat_id))
        material_id = cursor.lastrowid

        for media in user_data[chat_id]['files']:
            cursor.execute("INSERT INTO files (material_id, file_id, user_id) VALUES (?, ?, ?)", (material_id, media.media, chat_id))

        conn.commit()
        bot.reply_to(message, "Материал успешно добавлен!")
        user_data.pop(chat_id)
    else:
        msg = bot.reply_to(message, "Пожалуйста, отправьте документ или напишите /done, чтобы завершить.")
        bot.register_next_step_handler(msg, process_files_step)


# Пагинация для списка материалов
def generate_materials_markup(page=0, page_size=2):
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
    bot.send_message(message.chat.id, "Учебные материалы:", reply_markup=markup)


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
        media = [types.InputMediaDocument(file_id[0]) for file_id in files]
        if media:
            bot.send_media_group(call.message.chat.id, media)
    else:
        bot.send_message(call.message.chat.id, "Материал не найден.")

@bot.callback_query_handler(func=lambda call: call.data.endswith('_ctg'))
def choose_categories_handler(call):
    chat_id = call.message.chat.id
    user_data[chat_id]['category'] = call.data.split('_')[0]
    user_data[chat_id] = {'files': []}
    msg = bot.reply_to(call.message, "Введите название материала:")
    bot.register_next_step_handler(msg, process_title_step)



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
            media = [types.InputMediaDocument(file_id[0]) for file_id in files]
            if media:
                bot.send_media_group(message.chat.id, media)
    else:
        bot.reply_to(message, "Ничего не найдено по вашему запросу.")

@bot.inline_handler(lambda query: len(query.query) > 0)
def query_text(inline_query):
    query = inline_query.query
    results = []
    
    cursor.execute("SELECT id, title FROM materials WHERE title LIKE ? OR description LIKE ?",
                   ('%' + query + '%', '%' + query + '%'))
    materials = cursor.fetchall()
    
    for material in materials:
        material_id, title = material
        cursor.execute("SELECT file_id FROM files WHERE material_id=?", (material_id,))
        files = cursor.fetchall()
        
        for file in files:
            file_id = file[0]
            unique_id = f"{material_id}"  # Изменено для уникальности
            
            results.append(types.InlineQueryResultDocument(
                id=unique_id,
                title=title,
                document_url=file_id,  # Используем file_id напрямую
                mime_type="application/octet-stream",  # Можно изменить в зависимости от типа файла
                description="Нажмите, чтобы отправить файл"
            ))
    
    bot.answer_inline_query(inline_query.id, results)

def печать(value: any) -> None:
    print(value)


if __name__ == "__main__":
    печать('bot starting')
    bot.infinity_polling()
