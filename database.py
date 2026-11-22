import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_data.db")

def init_db():
    """Initializes the database schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            secret_key TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_cache (
            user_id INTEGER PRIMARY KEY,
            last_action TEXT,
            cache_data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_history_record(user_id: int, secret_key: str, otp_code: str):
    """Saves a 2FA generation record to history."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        cursor.execute("""
            INSERT INTO history (user_id, secret_key, otp_code, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, secret_key, otp_code, now_str))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving history: {e}")

def get_user_history(user_id: int, limit: int = 10):
    """Retrieves the recent history records for a user."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, secret_key, otp_code, created_at
            FROM history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [
            {"id": r[0], "secret_key": r[1], "otp_code": r[2], "created_at": r[3]}
            for r in rows
        ]
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []

def get_user_history_count(user_id: int) -> int:
    """Gets total number of history records for user."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM history WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(f"Error fetching count: {e}")
        return 0

def clear_user_history(user_id: int) -> bool:
    """Clears all history records for a user."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error clearing history: {e}")
        return False

def update_user_cache(user_id: int, action: str, data: str = ""):
    """Updates user session cache."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        cursor.execute("""
            INSERT INTO user_cache (user_id, last_action, cache_data, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                last_action = excluded.last_action,
                cache_data = excluded.cache_data,
                updated_at = excluded.updated_at
        """, (user_id, action, data, now_str))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating cache: {e}")

def clear_user_cache(user_id: int) -> bool:
    """Clears user session cache."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_cache WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return False
