import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from assistant import Ticket, WorkAssistant, WorkloadAnalysis, LLMClient
from core.session_manager import SessionManager


def _make_ticket(key: str, description: str = "") -> Ticket:
    now = datetime.now()
    return Ticket(
        key=key,
        summary=f"Summary {key}",
        description=description,
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


def test_analyze_dependencies_detects_references():
    t1 = _make_ticket("T1", description="Blocked by T2 and relates to T3")
    t2 = _make_ticket("T2")
    t3 = _make_ticket("T3")
    client = LLMClient()
    deps = client.analyze_dependencies([t1, t2, t3])
    assert deps == {"T1": ["T2", "T3"]}


def test_dependency_cache(tmp_path):
    t1 = _make_ticket("T1", description="See T2 for details")
    t2 = _make_ticket("T2")
    jira = MagicMock()
    jira.get_my_tickets.return_value = [t1, t2]

    analysis = WorkloadAnalysis(
        top_priority=t1,
        priority_reasoning="",
        next_steps=[],
        can_help_with=[],
        other_notable=[],
        summary="Focus on T1",
    )
    llm = MagicMock()
    llm.analyze_workload.return_value = analysis
    llm.analyze_dependencies.return_value = {"T1": ["T2"]}

    session_file = tmp_path / "session.json"
    sm = SessionManager(str(session_file))

    assistant = WorkAssistant(jira_client=jira, llm_client=llm, session_manager=sm)
    assistant._display_analysis = MagicMock()
    assistant._display_dependencies = MagicMock()
    assistant._interactive_session = MagicMock()

    with patch("assistant.Confirm.ask", return_value=True):
        assistant.start_session()
    llm.analyze_dependencies.assert_called_once()
    assert assistant.current_dependencies == {"T1": ["T2"]}

    sm.set_current_focus("T1")
    assistant._focus_on_ticket = MagicMock()

    llm.analyze_dependencies.reset_mock()
    with patch("assistant.Confirm.ask", return_value=True):
        assistant.start_session()
    llm.analyze_dependencies.assert_not_called()
    assert assistant.current_dependencies == {"T1": ["T2"]}
