from storage.db import get_connection

def has_active_session(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT active FROM sessions WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row and row[0] == 1)

def start_session(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO sessions (user_id, active) VALUES (?, 1)",
        (user_id,)
    )
    conn.commit()
    conn.close()

def end_session(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO sessions (user_id, active) VALUES (?, 0)",
        (user_id,)
    )
    conn.commit()
    conn.close()

def online_count() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sessions WHERE active = 1")
    count = cur.fetchone()[0]
    conn.close()
    return count