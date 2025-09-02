import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from assistant import LLMClient, Ticket, WorkloadAnalysis, WorkAssistant


class AnalysisCacheTests(unittest.TestCase):
    def setUp(self):
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
        self.analysis = WorkloadAnalysis(
            top_priority=self.ticket,
            priority_reasoning="because",
            next_steps=[],
            can_help_with=[],
            other_notable=[],
            summary="summary",
        )

    def test_cache_hit_returns_previous_analysis(self):
        client = LLMClient()
        client._compute_analysis = MagicMock(return_value=self.analysis)
        first = client.analyze_workload([self.ticket])
        second = client.analyze_workload([self.ticket])
        self.assertIs(first, second)
        client._compute_analysis.assert_called_once()

    def test_cache_expiration_triggers_recompute(self):
        client = LLMClient()
        client._compute_analysis = MagicMock(return_value=self.analysis)
        client.analyze_workload([self.ticket])
        client._cache_time -= timedelta(hours=25)
        client.analyze_workload([self.ticket])
        self.assertEqual(client._compute_analysis.call_count, 2)

    def test_re_analyze_command_clears_cache(self):
        client = LLMClient()
        client._compute_analysis = MagicMock(return_value=self.analysis)
        assistant = WorkAssistant(jira_client=MagicMock(), llm_client=client)
        assistant.current_tickets = [self.ticket]
        assistant.current_analysis = client.analyze_workload([self.ticket])
        assistant._handle_user_input("re analyze")
        self.assertEqual(client._compute_analysis.call_count, 2)


if __name__ == "__main__":
    unittest.main()
