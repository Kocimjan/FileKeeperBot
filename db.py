import sqlite3


class database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.sql = self.conn.cursor()

    def execute(self, query, *params):
        if params is None:
            self.sql.execute(query)
            data = self.sql.fetchall()
        else:
            self.sql.execute(query, params)
            data = self.sql.fetchall()
        if data:
            return data

    def close(self):
        self.conn.close()
