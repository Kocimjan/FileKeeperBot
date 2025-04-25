
-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    is_admin BOOLEAN DEFAULT 0,
    max_file_size INTEGER DEFAULT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица категорий
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- Таблица файлов
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT NOT NULL,
    file_name TEXT,
    file_size INTEGER,
    mime_type TEXT,
    uploader_id INTEGER NOT NULL,
    category_id INTEGER,
    is_public BOOLEAN DEFAULT 0,
    downloads_count INTEGER DEFAULT 0,
    description TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploader_id) REFERENCES users(user_id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Таблица тегов
CREATE TABLE IF NOT EXISTS file_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id)
);

-- Таблица удалённых файлов
CREATE TABLE IF NOT EXISTS deleted_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    deleted_by_user_id INTEGER,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (deleted_by_user_id) REFERENCES users(user_id)
);
