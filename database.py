import sqlite3
import datetime
from typing import List, Dict, Any

DB_NAME = "reminders.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    """Create the reminders table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY,
            task TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def load_reminders() -> List[Dict[str, Any]]:
    """Load all reminders from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, task, timestamp, status FROM reminders")
    rows = cursor.fetchall()
    conn.close()

    reminders = []
    for row in rows:
        reminders.append({
            "id": row[0],
            "task": row[1],
            "timestamp": datetime.datetime.fromisoformat(row[2]),
            "status": row[3],
        })
    return reminders

def save_reminders(reminders: List[Dict[str, Any]]):
    """Replace all reminders in the database with the current list."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders")  # clear old data

    for r in reminders:
        cursor.execute(
            "INSERT INTO reminders (id, task, timestamp, status) VALUES (?, ?, ?, ?)",
            (r["id"], r["task"], r["timestamp"].isoformat(), r["status"])
        )
    conn.commit()
    conn.close()