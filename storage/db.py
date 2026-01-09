import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "db.sqlite"


def get_connection():
    return sqlite3.connect(DB_PATH, isolation_level=None)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT
    )
    """)

    # CREDITS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS credits (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER NOT NULL DEFAULT 0
    )
    """)

    # SESSIONS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        user_id INTEGER PRIMARY KEY,
        active INTEGER NOT NULL DEFAULT 0
    )
    """)

    # BANS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bans (
        user_id INTEGER PRIMARY KEY,
        reason TEXT,
        banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # GATES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS gate_state (
        gate_key TEXT PRIMARY KEY,
        enabled INTEGER NOT NULL DEFAULT 1,
        max_cards INTEGER NOT NULL DEFAULT 200,
        cost_per_card INTEGER NOT NULL DEFAULT 1
    )
    """)

    # CODES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS codes (
        code TEXT PRIMARY KEY,
        credits INTEGER NOT NULL,
        max_uses INTEGER NOT NULL,
        used_count INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS code_redeems (
        code TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (code, user_id)
    )
    """)

    # BUY
    cur.execute("""
    CREATE TABLE IF NOT EXISTS buy_packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        credits INTEGER NOT NULL,
        stars INTEGER NOT NULL,
        bonus INTEGER NOT NULL DEFAULT 0,
        active INTEGER NOT NULL DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS buy_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        credits INTEGER NOT NULL,
        stars INTEGER NOT NULL,
        bonus INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()