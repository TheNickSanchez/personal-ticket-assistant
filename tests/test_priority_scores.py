import unittest
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from assistant import LLMClient, Ticket


class PriorityScoreTests(unittest.TestCase):
    def setUp(self):
        self.client = LLMClient()

    def _make_ticket(self, key: str, priority: str) -> Ticket:
        now = datetime.now()
        return Ticket(
            key=key,
            summary="",
            description="",
            priority=priority,
            status="Open",
            assignee=None,
            created=now,
            updated=now,
            comments_count=0,
            labels=[],
            issue_type="Bug",
            raw_data={},
        )

    def test_highest_label(self):
        high = self._make_ticket("H", "High")
        highest = self._make_ticket("HI", " Highest ")
        analysis = self.client._fallback_analysis([high, highest])
        self.assertEqual(analysis.top_priority.key, "HI")

    def test_p1_critical_label(self):
        high = self._make_ticket("H", "High")
        critical = self._make_ticket("C", "p1 - critical")
        analysis = self.client._fallback_analysis([high, critical])
        self.assertEqual(analysis.top_priority.key, "C")

    def test_p0_label(self):
        p1 = self._make_ticket("P1", "P1")
        p0 = self._make_ticket("P0", "p0")
        analysis = self.client._fallback_analysis([p1, p0])
        self.assertEqual(analysis.top_priority.key, "P0")


if __name__ == "__main__":
    unittest.main()

