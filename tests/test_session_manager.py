import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from assistant import Ticket, WorkAssistant, WorkloadAnalysis
from session_manager import SessionManager
from cache import Cache


class SessionManagerTests(unittest.TestCase):
    def setUp(self):
        now = datetime.now()
        self.ticket = Ticket(
            key="T1",
            summary="s",
            description="d",
            priority="P2",
            status="Open",
            assignee=None,
            created=now,
            updated=now,
            comments_count=0,
            labels=[],
            issue_type="Bug",
            raw_data={},
        )
        self.ticket_dict = {
            "key": "T1",
            "summary": "s",
            "description": "d",
            "priority": "P2",
            "status": "Open",
            "assignee": None,
            "created": now.isoformat(),
            "updated": now.isoformat(),
            "comments_count": 0,
            "labels": [],
            "issue_type": "Bug",
            "raw_data": {},
        }
        self.cache_file = "test_session.json"
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    def tearDown(self):
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    def test_last_scan_persisted(self):
        sm = SessionManager(cache=Cache(self.cache_file))
        self.assertIsNone(sm.last_scan)
        sm.update_session([self.ticket])
        self.assertIsNotNone(sm.last_scan)
        sm2 = SessionManager(cache=Cache(self.cache_file))
        self.assertIsNotNone(sm2.last_scan)

    def test_start_session_uses_cached_when_recent(self):
        cache = Cache(self.cache_file)
        cache.set("session", {"last_scan": datetime.now().isoformat(), "tickets": [self.ticket_dict]})
        sm = SessionManager(cache)
        jira = MagicMock()
        llm = MagicMock()
        llm.analyze_workload.return_value = WorkloadAnalysis(
            top_priority=self.ticket,
            priority_reasoning="",
            next_steps=[],
            can_help_with=[],
            other_notable=[],
            summary="",
        )
        assistant = WorkAssistant(jira_client=jira, llm_client=llm, session_manager=sm)
        assistant._display_analysis = MagicMock()
        assistant._interactive_session = MagicMock()
        with patch("assistant.Confirm.ask", return_value=True):
            assistant.start_session()
        jira.get_my_tickets.assert_not_called()

    def test_start_session_rescans_when_old(self):
        cache = Cache(self.cache_file)
        old_time = datetime.now() - timedelta(hours=25)
        cache.set("session", {"last_scan": old_time.isoformat(), "tickets": [self.ticket_dict]})
        sm = SessionManager(cache)
        jira = MagicMock()
        jira.get_my_tickets.return_value = [self.ticket]
        llm = MagicMock()
        llm.analyze_workload.return_value = WorkloadAnalysis(
            top_priority=self.ticket,
            priority_reasoning="",
            next_steps=[],
            can_help_with=[],
            other_notable=[],
            summary="",
        )
        assistant = WorkAssistant(jira_client=jira, llm_client=llm, session_manager=sm)
        assistant._display_analysis = MagicMock()
        assistant._interactive_session = MagicMock()
        with patch("assistant.Confirm.ask", return_value=True):
            assistant.start_session()
        jira.get_my_tickets.assert_called_once()


if __name__ == "__main__":
    unittest.main()
from datetime import datetime, timedelta
from session_manager import SessionManager


def test_new_session_default_state(tmp_path):
    session_file = tmp_path / "session.json"
    manager = SessionManager(str(session_file))
    assert manager.last_scan is None
    assert manager.current_focus is None


def test_save_and_reload_state(tmp_path):
    session_file = tmp_path / "session.json"
    manager = SessionManager(str(session_file))
    now = datetime.now()
    manager.last_scan = now
    manager.current_focus = "TICKET-1"
    manager.save()

    reloaded = SessionManager(str(session_file))
    assert reloaded.last_scan == now
    assert reloaded.current_focus == "TICKET-1"


def test_within_24_hours_boundaries(tmp_path):
    session_file = tmp_path / "session.json"
    manager = SessionManager(str(session_file))
    now = datetime.now()

    manager.last_scan = now - timedelta(hours=23, minutes=59)
    assert manager.within_24_hours()

    manager.last_scan = now - timedelta(hours=24)
    assert not manager.within_24_hours()

    manager.last_scan = now - timedelta(hours=24, minutes=1)
    assert not manager.within_24_hours()
