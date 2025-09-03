import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from assistant import LLMClient, Ticket, SessionManager

class FeedbackLoopTests(unittest.TestCase):
    def setUp(self):
        os.environ["CACHE_FILE"] = "test_cache.json"
        os.environ["LLM_PROVIDER"] = "openai"
        self.session_file = "test_session.json"
        for f in ["test_cache.json", self.session_file]:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass
        self.session = SessionManager(self.session_file)
        self.client = LLMClient(self.session)
        now = datetime.now()
        self.ticket = Ticket(
            key="T1",
            summary="",
            description="",
            priority="P1",
            status="Open",
            assignee=None,
            created=now,
            updated=now,
            comments_count=0,
            labels=[],
            issue_type="Bug",
            raw_data={},
        )

    def tearDown(self):
        for f in ["test_cache.json", self.session_file]:
            if os.path.exists(f):
                os.remove(f)
        del os.environ["CACHE_FILE"]
        del os.environ["LLM_PROVIDER"]

    def _mock_resp(self, text: str):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])

    def test_positive_feedback_loop(self):
        with patch("assistant.openai.chat.completions.create", return_value=self._mock_resp("first")):
            self.client.suggest_action(self.ticket, "ctx")
        self.session.add_feedback(self.ticket.key, "ctx", "good")
        with patch("assistant.openai.chat.completions.create", return_value=self._mock_resp("second")) as mock_create:
            self.client.suggest_action(self.ticket, "ctx", force_refresh=True)
            prompt = mock_create.call_args[1]["messages"][0]["content"]
            self.assertIn("good", prompt)

    def test_negative_feedback_loop(self):
        with patch("assistant.openai.chat.completions.create", return_value=self._mock_resp("first")):
            self.client.suggest_action(self.ticket, "ctx")
        self.session.add_feedback(self.ticket.key, "ctx", "bad")
        with patch("assistant.openai.chat.completions.create", return_value=self._mock_resp("second")) as mock_create:
            self.client.suggest_action(self.ticket, "ctx", force_refresh=True)
            prompt = mock_create.call_args[1]["messages"][0]["content"]
            self.assertIn("bad", prompt)

if __name__ == "__main__":
    unittest.main()
