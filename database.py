import sqlite3
import os
from datetime import datetime

DB_NAME = os.environ.get("DB_NAME", "shortener.db")

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            created_at TEXT NOT NULL,
            click_count INTEGER DEFAULT 0
         )
    """)
    conn.commit()
    conn.close()


def create_url(short_code, original_url):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO urls (short_code, original_url, created_at) VALUES (?, ?, ?)",
        (short_code, original_url, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def get_original_url(short_code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT original_url FROM urls WHERE short_code = ?",
        (short_code,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def increment_click_count(short_code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE urls SET click_count = click_count + 1 WHERE short_code = ?",
        (short_code,)
    )
    conn.commit()
    conn.close()
