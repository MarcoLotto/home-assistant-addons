import sqlite3
from common import BASE_TARGET_PATH

# Create a new SQLite database and set up tables
DATABASE_NAME = BASE_TARGET_PATH + 'database.db'

def init_db():
    with sqlite3.connect(DATABASE_NAME) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            scheduled_task_id INTEGER PRIMARY KEY,
            task_id INTEGER,
            scheduled_date TEXT,
            user_id INTEGER,
            status TEXT
        )
        """)

def open_db_session():
    return sqlite3.connect(DATABASE_NAME)
