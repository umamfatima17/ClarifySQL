import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import session_store


class TestSessionStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_sessions.db"

        def connect_test_db():
            connection = sqlite3.connect(self.db_path)
            connection.row_factory = sqlite3.Row
            return connection

        self.connection_patch = patch(
            "core.session_store.get_connection",
            side_effect=connect_test_db,
        )
        self.connection_patch.start()
        session_store.initialize_session_tables()

    def tearDown(self):
        self.connection_patch.stop()
        self.temp_dir.cleanup()

    def test_create_and_retrieve_session(self):
        session_id = session_store.create_session(
            "Which product generated the most revenue?",
            context={"step": 1},
        )

        session = session_store.get_session(session_id)

        self.assertIsNotNone(session)
        self.assertEqual(session["status"], "pending")
        self.assertEqual(session["context"], {"step": 1})
        self.assertEqual(len(session["messages"]), 1)
        self.assertEqual(
            session["messages"][0]["content"],
            "Which product generated the most revenue?",
        )

    def test_messages_are_persisted_in_order(self):
        session_id = session_store.create_session("Show top products")
        session_store.add_session_message(
            session_id, "assistant", "Choose a metric."
        )
        session_store.add_session_message(
            session_id, "user", "Revenue"
        )

        session = session_store.get_session(session_id)

        self.assertEqual(
            [message["content"] for message in session["messages"]],
            ["Show top products", "Choose a metric.", "Revenue"],
        )

    def test_context_update_preserves_completed_status(self):
        session_id = session_store.create_session("Show revenue")
        session_store.update_session(session_id, status="completed")

        session_store.update_session(
            session_id,
            context={"answer": "Revenue"},
        )

        session = session_store.get_session(session_id)
        self.assertEqual(session["status"], "completed")
        self.assertEqual(session["context"], {"answer": "Revenue"})

    def test_empty_question_is_rejected(self):
        with self.assertRaises(ValueError):
            session_store.create_session("   ")

    def test_unknown_session_returns_none(self):
        self.assertIsNone(session_store.get_session("unknown-session"))


if __name__ == "__main__":
    unittest.main()
