import sqlite3
from datetime import datetime

db = sqlite3.connect("qarzdaftar.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS foydalanuvchilar (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    fullname TEXT,
    phone TEXT,
    password TEXT,
    address TEXT,
    registered_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_debt DECIMAL
)
""")
db.commit()
