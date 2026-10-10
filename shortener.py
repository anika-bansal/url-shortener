import random
import string
import sqlite3
from database import get_connection, create_url

def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def generate_unique_short_code(length=6):
    while True:
        code = generate_short_code(length)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM urls WHERE short_code =?", (code,))
        exists = cursor.fetchone()
        conn.close()
        if not exists:
            return code

def create_url_with_retry(original_url, max_attempts=5):
    for _ in range(max_attempts):
        code = generate_unique_short_code()
        try:
            create_url(code, original_url)
            return code
        except sqlite3.IntegrityError:
            continue
    raise RuntimeError("Could not generate a unique short code after several attempts")
