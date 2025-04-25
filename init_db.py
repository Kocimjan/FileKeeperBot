import sqlite3


def init_db(db_path='filecloud.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        with open('schema.sql', 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
        conn.commit()


if __name__ == '__main__':
    init_db()
    print('Database initialized.')
