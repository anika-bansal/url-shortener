import random
import string
from database import get_connection

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
