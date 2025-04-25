import sqlite3
from config import DB_PATH


def connect_db():
    return sqlite3.connect(DB_PATH)


def create_user(user_id, username, first_name):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                (user_id, username, first_name))
    conn.commit()
    conn.close()


def save_file(file_id, file_name, file_size, mime_type, uploader_id, is_public, category_id, description=''):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO files (file_id, file_name, file_size, mime_type, uploader_id, is_public, category_id, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (file_id, file_name, file_size, mime_type, uploader_id, is_public, category_id, description))
    conn.commit()
    conn.close()


def save_file_tags(file_id, tags):
    conn = connect_db()
    cur = conn.cursor()
    for tag in tags:
        cur.execute("INSERT INTO file_tags (file_id, tag) VALUES (?, ?)", (file_id, tag))
    conn.commit()
    conn.close()


def get_categories():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    conn.close()
    return categories


def is_admin(user_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row and row[0] == 1


def delete_category_by_id(cat_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()


def add_category(name):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def find_user_by_id_or_username(identifier):
    conn = connect_db()
    cur = conn.cursor()
    if identifier.isdigit():
        cur.execute("SELECT * FROM users WHERE user_id = ?", (int(identifier),))
    else:
        cur.execute("SELECT * FROM users WHERE username = ?", (identifier,))
    user = cur.fetchone()
    conn.close()
    return user


def get_user_file_stats(user_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(file_size), SUM(CASE WHEN is_public=0 THEN 1 ELSE 0 END), "
                "SUM(CASE WHEN is_public=1 THEN 1 ELSE 0 END) FROM files WHERE uploader_id = ?",
                (user_id,))
    count, total_size, private, public = cur.fetchone()
    conn.close()
    return {
        'count': count or 0,
        'size': total_size or 0,
        'private': private or 0,
        'public': public or 0
    }


def set_user_limit(user_id, limit):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET max_file_size = ? WHERE user_id = ?", (limit, user_id))
    conn.commit()
    conn.close()


def get_user_by_id(user_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT first_name, username, max_file_size FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return {
        'first_name': row[0],
        'username': row[1],
        'max_file_size': row[2]
    }


def format_size(bytes_amount):
    if not bytes_amount:
        return "по умолчанию"
    elif bytes_amount < 1024**2:
        return f"{bytes_amount/1024:.2f} KB"
    elif bytes_amount < 1024**3:
        return f"{bytes_amount/1024**2:.2f} MB"
    else:
        return f"{bytes_amount/1024**3:.2f} GB"


def set_admin(user_id: int, is_admin=True):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_admin = ? WHERE user_id = ?", (int(is_admin), user_id))
    conn.commit()
    conn.close()


def get_public_files_paginated(page, per_page=5):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, file_id, file_name, file_size, uploader_id
        FROM files
        WHERE is_public = 1
        ORDER BY uploaded_at DESC
        LIMIT ? OFFSET ?
    """, (per_page, page * per_page))
    rows = cur.fetchall()
    conn.close()
    return [
        {
            'id': r[0],
            'file_id': r[1],
            'file_name': r[2],
            'file_size': r[3],
            'uploader_id': r[4]
        } for r in rows
    ]


def get_file_uploader_name(user_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_file_by_db_id(file_db_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT file_id FROM files WHERE id = ?", (file_db_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {'file_id': row[0]}
    return None
