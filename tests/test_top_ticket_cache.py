import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import Ticket, WorkloadAnalysis
from core.work_assistant import WorkAssistant
from core.session_manager import SessionManager


def _make_ticket(key: str) -> Ticket:
    now = datetime.now()
    return Ticket(
        key=key,
        summary=f"Summary {key}",
        description="",
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


def test_cached_summary_preserves_top_ticket(tmp_path):
    t1 = _make_ticket("T1")
    t2 = _make_ticket("T2")

    jira = MagicMock()
    jira.get_my_tickets.return_value = [t1, t2]

    analysis = WorkloadAnalysis(
        top_priority=t2,
        priority_reasoning="",
        next_steps=[],
        can_help_with=[],
        other_notable=[],
        summary="Focus on T2",
    )
    llm = MagicMock()
    llm.analyze_workload.return_value = analysis
    llm.analyze_dependencies.return_value = {}

    session_file = tmp_path / "session.json"
    sm = SessionManager(str(session_file))

    assistant = WorkAssistant(jira_client=jira, llm_client=llm, session_manager=sm)
    assistant._display_analysis = MagicMock()
    assistant._display_dependencies = MagicMock()
    assistant._interactive_session = MagicMock()

    # First run populates the cache
    with patch("core.work_assistant.Confirm.ask", return_value=True):
        assistant.start_session()

    # Second run should use cached analysis and not call the LLM
    llm.analyze_workload.reset_mock()
    with patch("core.work_assistant.Confirm.ask", return_value=True):
        assistant.start_session()

    llm.analyze_workload.assert_not_called()
    assert assistant.current_analysis.top_priority.key == "T2"
    assert "T2" in assistant.current_analysis.summary

