import sqlite3

DATABASE_URL = "meal_log.db"

def create_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

def update_schema():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users);")
    columns = [column["name"] for column in cursor.fetchall()]
    if "water_goal" not in columns:
        cursor.execute('''ALTER TABLE users ADD COLUMN water_goal INTEGER DEFAULT 2000;''')
        conn.commit()
    conn.close()

update_schema()

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
    conn.commit()
    conn.close()

create_tables()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import csv
from io import StringIO

app = FastAPI()

class SignUpRequest(BaseModel):
    name: str
    password: str
    age: int
    weight: float
    calorie_goal: int

class LoginRequest(BaseModel):
    name: str
    password: str

class MealLogRequest(BaseModel):
    user_id: int
    meal_name: str
    calories: int
    protein: float
    carbs: float
    fats: float

class WaterLogRequest(BaseModel):
    user_id: int
    water_intake: int

class MealUpdateRequest(BaseModel):
    meal_name: str
    calories: int
    protein: float
    carbs: float
    fats: float

@app.post("/signup")
def sign_up(user: SignUpRequest):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''INSERT INTO users (name, password, age, weight, calorie_goal)
                          VALUES (?, ?, ?, ?, ?)''', (user.name, user.password, user.age, user.weight, user.calorie_goal))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists.")
    finally:
        conn.close()
    return {"message": "Account created successfully!"}

@app.post("/login")
def login(user: LoginRequest):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT id, name, age, weight, calorie_goal 
                      FROM users WHERE name = ? AND password = ?''', (user.name, user.password))
    db_user = cursor.fetchone()
    conn.close()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials.")
    return {"id": db_user["id"], "name": db_user["name"], "age": db_user["age"], "weight": db_user["weight"], "calorie_goal": db_user["calorie_goal"]}

@app.post("/log_meal")
def log_meal(meal: MealLogRequest):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO meals (user_id, meal_name, calories, protein, carbs, fats)
                      VALUES (?, ?, ?, ?, ?, ?)''', (meal.user_id, meal.meal_name, meal.calories, meal.protein, meal.carbs, meal.fats))
    conn.commit()
    conn.close()
    return {"message": "Meal logged successfully!"}

@app.put("/update_meal/{meal_id}")
def update_meal(meal_id: int, meal: MealUpdateRequest):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''UPDATE meals SET meal_name = ?, calories = ?, protein = ?, carbs = ?, fats = ?
                      WHERE id = ?''', (meal.meal_name, meal.calories, meal.protein, meal.carbs, meal.fats, meal_id))
    conn.commit()
    conn.close()
    return {"message": "Meal updated successfully!"}

@app.get("/meals/{user_id}")
def get_meals(user_id: int):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT meal_name, calories, protein, carbs, fats, date_logged 
                      FROM meals WHERE user_id = ?''', (user_id,))
    meals = cursor.fetchall()
    conn.close()
    return [dict(meal) for meal in meals]

@app.get("/weekly_summary/{user_id}")
def weekly_summary(user_id: int):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT date_logged, SUM(calories) as total_calories, SUM(protein) as total_protein,
                      SUM(carbs) as total_carbs, SUM(fats) as total_fats
                      FROM meals WHERE user_id = ? AND date_logged >= DATE('now', '-6 days') GROUP BY date_logged''', (user_id,))
    summary = cursor.fetchall()
    conn.close()
    return [dict(day) for day in summary]

@app.post("/log_water")
def log_water(water: WaterLogRequest):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO water_logs (user_id, water_intake, date_logged)
                      VALUES (?, ?, DATE('now'))''', (water.user_id, water.water_intake))
    conn.commit()
    conn.close()
    return {"message": "Water intake logged successfully!"}

@app.get("/water/{user_id}")
def get_water_log(user_id: int):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT SUM(water_intake) as total_water 
                      FROM water_logs WHERE user_id = ? AND date_logged = DATE('now')''', (user_id,))
    total_water = cursor.fetchone()["total_water"]
    conn.close()
    return {"total_water": total_water}

@app.get("/download_meals/{user_id}")
def download_meals(user_id: int):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT meal_name, calories, protein, carbs, fats, date_logged 
                      FROM meals WHERE user_id = ?''', (user_id,))
    meals = cursor.fetchall()
    conn.close()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Meal Name", "Calories", "Protein", "Carbs", "Fats", "Date Logged"])
    writer.writerows([tuple(meal) for meal in meals])
    output.seek(0)
    return {"csv": output.getvalue()}
