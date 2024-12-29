import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

DATABASE_URL = "meal_log.db"


def create_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn



def create_tables():
    conn = create_connection()
    cursor = conn.cursor()


    cursor.execute("PRAGMA table_info(meals);")
    columns = [column["name"] for column in cursor.fetchall()]
    if "category" not in columns:
        cursor.execute('''ALTER TABLE meals ADD COLUMN category TEXT;''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        age INTEGER NOT NULL,
                        weight INTEGER NOT NULL,
                        calorie_goal INTEGER NOT NULL
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

    conn.commit()
    conn.close()


create_tables()


def fetch_meal_history(user_id, date=None, category=None):
    conn = create_connection()
    cursor = conn.cursor()


    query = '''SELECT id, meal_name, category, calories, protein, carbs, fats, date_logged 
               FROM meals WHERE user_id = ?'''
    params = [user_id]

    if date:
        query += ' AND date_logged = ?'
        params.append(date)

    if category:
        query += ' AND category = ?'
        params.append(category)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_meal(meal_id, meal_name, category, calories, protein, carbs, fats):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE meals 
        SET meal_name = ?, category = ?, calories = ?, protein = ?, carbs = ?, fats = ? 
        WHERE id = ?
    ''', (meal_name, category, calories, protein, carbs, fats, meal_id))
    conn.commit()
    conn.close()


def log_water(user_id, water_intake):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO water_logs (user_id, water_intake, date_logged)
        VALUES (?, ?, DATE('now'))
    ''', (user_id, water_intake))
    conn.commit()
    conn.close()


def fetch_water_logs(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT SUM(water_intake) as total_water FROM water_logs WHERE user_id = ? AND date_logged = DATE("now")',
        (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result['total_water'] if result['total_water'] else 0


def fetch_weekly_summary(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date_logged, SUM(calories) as total_calories, SUM(protein) as total_protein, 
               SUM(carbs) as total_carbs, SUM(fats) as total_fats
        FROM meals
        WHERE user_id = ? AND date_logged >= DATE('now', '-6 days')
        GROUP BY date_logged
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def download_history_as_csv(user_id):
    meals = fetch_meal_history(user_id)
    df = pd.DataFrame(meals,
                      columns=["id", "meal_name", "category", "calories", "protein", "carbs", "fats", "date_logged"])
    csv = df.to_csv(index=False)
    return csv


st.title("Meal Tracker App")
menu = ["Login", "Sign Up", "Dashboard"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE name = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            st.success("Logged in successfully!")
            st.session_state["user_id"] = user["id"]
        else:
            st.error("Invalid username or password.")

elif choice == "Sign Up":
    st.subheader("Sign Up")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    age = st.number_input("Age", min_value=1, max_value=120)
    weight = st.number_input("Weight (kg)", min_value=1.0)
    calorie_goal = st.number_input("Daily Calorie Goal", min_value=500)
    water_goal = st.number_input("Daily Water Goal (ml)", min_value=500)
    if st.button("Sign Up"):
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (name, password, age, weight, calorie_goal, water_goal)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, password, age, weight, calorie_goal, water_goal))
            conn.commit()
            st.success("Account created successfully!")
        except sqlite3.IntegrityError:
            st.error("Username already exists.")
        conn.close()

elif choice == "Dashboard":
    if "user_id" not in st.session_state:
        st.warning("Please log in first.")
    else:
        user_id = st.session_state["user_id"]
        tab1, tab2, tab3 = st.tabs(["Log Meals", "Meal History", "Water Intake"])

        with tab1:
            meal_name = st.text_input("Meal Name")
            category = st.selectbox("Category", ["Breakfast", "Lunch", "Dinner", "Snack"])
            calories = st.number_input("Calories", min_value=0)
            protein = st.number_input("Protein (g)", min_value=0.0)
            carbs = st.number_input("Carbs (g)", min_value=0.0)
            fats = st.number_input("Fats (g)", min_value=0.0)
            if st.button("Log Meal"):
                conn = create_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO meals (user_id, meal_name, category, calories, protein, carbs, fats)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, meal_name, category, calories, protein, carbs, fats))
                conn.commit()
                conn.close()

        with tab2:
            date_filter = st.date_input("Filter by Date")
            category_filter = st.selectbox("Filter by Category", ["All", "Breakfast", "Lunch", "Dinner", "Snack"])
            selected_date = date_filter.strftime("%Y-%m-%d") if date_filter else None
            category_value = category_filter if category_filter != "All" else None
            meals = fetch_meal_history(user_id, selected_date, category_value)
            df = pd.DataFrame(meals,
                              columns=["id", "Meal Name", "Category", "Calories", "Protein", "Carbs", "Fats", "Date"])
            st.dataframe(df)

        with tab3:
            water_intake = st.number_input("Water Intake (ml)", min_value=0)
            if st.button("Log Water"):
                log_water(user_id, water_intake)
            total_water = fetch_water_logs(user_id)
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT water_goal FROM users WHERE id = ?", (user_id,))
            goal = cursor.fetchone()["water_goal"]
            conn.close()


            if goal > 0:
                progress = min(max(total_water / goal * 100, 0), 100)
            else:
                progress = 0


            st.progress(progress / 100)
            st.write(f"Today's Water Intake: {total_water} ml out of {goal} ml")

        st.subheader("Weekly Summary")
        summary = fetch_weekly_summary(user_id)
        if summary:
            dates = [row["date_logged"] for row in summary]
            calories = [row["total_calories"] for row in summary]
            plt.bar(dates, calories, color="blue")
            st.pyplot(plt)
