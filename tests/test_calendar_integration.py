import sys, os
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import Ticket, WorkloadAnalysis
from core.work_assistant import WorkAssistant
from core.session_manager import SessionManager
from integrations.calendar_client import CalendarEvent


def _make_ticket(key: str) -> Ticket:
    now = datetime.now()
    return Ticket(
        key=key,
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


def test_events_passed_to_llm(tmp_path):
    ticket = _make_ticket("T1")
    jira = MagicMock()
    jira.get_my_tickets.return_value = [ticket]

    start = datetime.now() + timedelta(hours=1)
    end = start + timedelta(hours=1)
    event = CalendarEvent(summary="Meeting", start=start, end=end)
    calendar = MagicMock()
    calendar.get_upcoming_events.return_value = [event]

    analysis = WorkloadAnalysis(
        top_priority=ticket,
        priority_reasoning="",
        next_steps=[],
        can_help_with=[],
        other_notable=[],
        summary="summary",
    )
    llm = MagicMock()
    llm.analyze_workload.return_value = analysis
    llm.analyze_dependencies.return_value = {}

    sm = SessionManager(str(tmp_path / "session.json"))
    assistant = WorkAssistant(jira_client=jira, llm_client=llm, session_manager=sm, calendar_client=calendar)
    assistant._display_analysis = MagicMock()
    assistant._interactive_session = MagicMock()

    with patch("core.work_assistant.Confirm.ask", return_value=False):
        assistant.start_session()

    llm.analyze_workload.assert_called_once()
    args, kwargs = llm.analyze_workload.call_args
    assert args[0] == [ticket]
    assert args[1] == [event]


def test_check_command_surfaces_events():
    start = datetime.now() + timedelta(hours=1)
    end = start + timedelta(hours=1)
    event = CalendarEvent(summary="Planning", start=start, end=end)
    calendar = MagicMock()
    calendar.get_upcoming_events.return_value = [event]

    assistant = WorkAssistant(jira_client=MagicMock(), llm_client=MagicMock(), calendar_client=calendar)

    from rich.console import Console
    sio = StringIO()
    with patch("core.work_assistant.console", Console(file=sio)):
        assistant._handle_user_input("check")
    output = sio.getvalue()
    assert "Planning" in output
    assert "Free until" in output
