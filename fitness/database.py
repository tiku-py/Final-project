import sqlite3

DATABASE_URL = "meal_log.db"

def create_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        age INTEGER NOT NULL,
                        weight INTEGER NOT NULL,
                        calorie_goal INTEGER NOT NULL,
                        water_goal INTEGER DEFAULT 2000
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS meals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        meal_name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        calories INTEGER NOT NULL,
                        protein REAL,
                        carbs REAL,
                        fats REAL,
                        date_logged DATE DEFAULT (DATE('now')),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS water_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        water_intake INTEGER NOT NULL,
                        date_logged DATE DEFAULT (DATE('now')),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        type TEXT NOT NULL,
                        time TEXT NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
