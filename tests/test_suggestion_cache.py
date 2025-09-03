import os
import json
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from core.llm_client import LLMClient
from core.models import Ticket

class SuggestionCacheTests(unittest.TestCase):
    def setUp(self):
        os.environ["CACHE_FILE"] = "test_cache.json"
        os.environ["LLM_PROVIDER"] = "openai"
        try:
            os.remove("test_cache.json")
        except FileNotFoundError:
            pass
        self.client = LLMClient()
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
        if os.path.exists("test_cache.json"):
            os.remove("test_cache.json")
        del os.environ["CACHE_FILE"]
        del os.environ["LLM_PROVIDER"]

    def _mock_resp(self, text: str):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])

    def test_cached_suggestion_reused(self):
        with patch("core.llm_client.openai.chat.completions.create", return_value=self._mock_resp("first")) as mock_create:
            first = self.client.suggest_action(self.ticket, "ctx")
            second = self.client.suggest_action(self.ticket, "ctx")
            self.assertEqual(first, "first")
            self.assertEqual(second, "first")
            self.assertEqual(mock_create.call_count, 1)

    def test_force_refresh(self):
        responses = [self._mock_resp("first"), self._mock_resp("second")]
        with patch("core.llm_client.openai.chat.completions.create", side_effect=responses) as mock_create:
            first = self.client.suggest_action(self.ticket, "ctx")
            second = self.client.suggest_action(self.ticket, "ctx", force_refresh=True)
            self.assertEqual(first, "first")
            self.assertEqual(second, "second")
            self.assertEqual(mock_create.call_count, 2)

    def test_cache_expiration(self):
        responses = [self._mock_resp("first"), self._mock_resp("second")]
        with patch("core.llm_client.openai.chat.completions.create", side_effect=responses) as mock_create:
            first = self.client.suggest_action(self.ticket, "ctx")
            key = f"{self.ticket.key}:ctx"
            cached = self.client.cache.get(key)
            cached["timestamp"] = (datetime.now() - timedelta(hours=25)).isoformat()
            self.client.cache.set(key, cached)
            second = self.client.suggest_action(self.ticket, "ctx")
            self.assertEqual(first, "first")
            self.assertEqual(second, "second")
            self.assertEqual(mock_create.call_count, 2)

if __name__ == "__main__":
    unittest.main()
