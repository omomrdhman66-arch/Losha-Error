import random
import string
from storage.db import get_connection

def generate_code():
    chars = string.ascii_uppercase + string.digits
    return "LOSHA-2026-" + ''.join(random.choices(chars, k=4))

def create_code(credits: int, max_uses: int) -> str:
    code = generate_code()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO codes (code, credits, max_uses, used_count)
        VALUES (?, ?, ?, 0)
        """,
        (code, credits, max_uses)
    )
    conn.commit()
    conn.close()
    return code