"""Persistent storage for ClarifySQL clarification sessions."""

import json
import uuid
from contextlib import closing
from datetime import datetime, timezone

from core.database import get_connection


def initialize_session_tables():
    """Create session tables without changing existing business tables."""
    with closing(get_connection()) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS clarification_sessions (
                    session_id TEXT PRIMARY KEY,
                    original_question TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    context_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS clarification_messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id)
                        REFERENCES clarification_sessions(session_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_clarification_messages_session
                ON clarification_messages(session_id, message_id)
                """
            )


def create_session(original_question, context=None):
    """Create a session and record the initial user question."""
    question = str(original_question or "").strip()
    if not question:
        raise ValueError("The original question cannot be empty.")

    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    context_json = json.dumps(context or {}, ensure_ascii=False)

    with closing(get_connection()) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO clarification_sessions
                (session_id, original_question, status, context_json,
                 created_at, updated_at)
                VALUES (?, ?, 'pending', ?, ?, ?)
                """,
                (session_id, question, context_json, now, now),
            )
            connection.execute(
                """
                INSERT INTO clarification_messages
                (session_id, role, content, created_at)
                VALUES (?, 'user', ?, ?)
                """,
                (session_id, question, now),
            )

    return session_id


def add_session_message(session_id, role, content):
    """Save a user or assistant message and update the session timestamp."""
    if role not in {"user", "assistant", "system"}:
        raise ValueError("Role must be user, assistant, or system.")

    message = str(content or "").strip()
    if not message:
        raise ValueError("Message content cannot be empty.")

    now = datetime.now(timezone.utc).isoformat()

    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO clarification_messages
                (session_id, role, content, created_at)
                SELECT session_id, ?, ?, ?
                FROM clarification_sessions
                WHERE session_id = ?
                """,
                (role, message, now, session_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("Clarification session was not found.")

            connection.execute(
                """
                UPDATE clarification_sessions
                SET updated_at = ?
                WHERE session_id = ?
                """,
                (now, session_id),
            )


def update_session(session_id, status=None, context=None):
    """Update session status and/or its JSON context."""
    allowed_statuses = {"pending", "completed", "error"}
    if status is not None and status not in allowed_statuses:
        raise ValueError("Status must be pending, completed, or error.")

    now = datetime.now(timezone.utc).isoformat()

    with closing(get_connection()) as connection:
        with connection:
            session = connection.execute(
                """
                SELECT status, context_json
                FROM clarification_sessions
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()

            if session is None:
                raise ValueError("Clarification session was not found.")

            context_json = (
                json.dumps(context, ensure_ascii=False)
                if context is not None
                else session["context_json"]
            )

            connection.execute(
                """
                UPDATE clarification_sessions
                SET status = ?, context_json = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (
                    status if status is not None else session["status"],
                    context_json,
                    now,
                    session_id,
                ),
            )


def get_session(session_id):
    """Retrieve a session and its messages for resuming later."""
    with closing(get_connection()) as connection:
        with connection:
            session = connection.execute(
                """
                SELECT *
                FROM clarification_sessions
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()

            if session is None:
                return None

            messages = connection.execute(
                """
                SELECT role, content, created_at
                FROM clarification_messages
                WHERE session_id = ?
                ORDER BY message_id
                """,
                (session_id,),
            ).fetchall()

            result = dict(session)
            result["context"] = json.loads(result.pop("context_json"))
            result["messages"] = [dict(message) for message in messages]
            return result




def list_pending_sessions():
    """List clarification sessions that can be resumed."""
    with closing(get_connection()) as connection:
        with connection:
            rows = connection.execute(
                """
                SELECT session_id, original_question, updated_at
                FROM clarification_sessions
                WHERE status = 'pending'
                ORDER BY updated_at DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]
