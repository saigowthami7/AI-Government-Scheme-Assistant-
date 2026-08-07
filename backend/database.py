"""
database.py
Owner: Member 2 - Backend Developer

Lightweight SQLite database setup for:
  - chat_sessions: one row per conversation (tracks the accumulated user profile)
  - chat_messages: every message exchanged, for history + follow-up questions

SQLite is used for simplicity during development/demo; swap the connection
string in `get_connection()` for Postgres/MySQL later without changing the
calling code much, since queries are plain SQL.
"""

import sqlite3
import json
import uuid
import os
from datetime import datetime
from typing import Optional, List, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), "scheme_assistant.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            profile_json TEXT DEFAULT '{}',
            preferred_language TEXT DEFAULT 'en',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,          -- 'user' or 'assistant'
            content TEXT NOT NULL,
            matched_schemes_json TEXT,   -- only populated for assistant messages
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
        )
    """)

    conn.commit()
    conn.close()
    print(f"[database] Initialized SQLite DB at {DB_PATH}")


def create_session() -> str:
    session_id = str(uuid.uuid4())
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_sessions (session_id, profile_json, created_at) VALUES (?, ?, ?)",
        (session_id, "{}", datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return session_id


def get_session_profile(session_id: str) -> Dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT profile_json FROM chat_sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return {}
    return json.loads(row["profile_json"])


def update_session_profile(session_id: str, profile: Dict, language: Optional[str] = None):
    conn = get_connection()
    if language:
        conn.execute(
            "UPDATE chat_sessions SET profile_json = ?, preferred_language = ? WHERE session_id = ?",
            (json.dumps(profile), language, session_id),
        )
    else:
        conn.execute(
            "UPDATE chat_sessions SET profile_json = ? WHERE session_id = ?",
            (json.dumps(profile), session_id),
        )
    conn.commit()
    conn.close()


def add_message(session_id: str, role: str, content: str, matched_schemes: Optional[List[Dict]] = None):
    conn = get_connection()
    conn.execute(
        """INSERT INTO chat_messages (message_id, session_id, role, content, matched_schemes_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            str(uuid.uuid4()),
            session_id,
            role,
            content,
            json.dumps(matched_schemes) if matched_schemes else None,
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_conversation_history(session_id: str, limit: int = 20) -> List[Dict]:
    """Returns history formatted for direct use as the LLM `messages` list."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT role, content FROM chat_messages
           WHERE session_id = ? ORDER BY created_at ASC LIMIT ?""",
        (session_id, limit),
    ).fetchall()
    conn.close()
    return [{"role": row["role"], "content": row["content"]} for row in rows]


if __name__ == "__main__":
    init_db()
