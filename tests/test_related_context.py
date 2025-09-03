import os
import sys
from datetime import datetime
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.work_assistant import WorkAssistant
from core.llm_client import LLMClient
from core.models import Ticket
from core.session_manager import SessionManager


def make_ticket(key: str, summary: str) -> Ticket:
    now = datetime.now()
    return Ticket(
        key=key,
        summary=summary,
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


def test_previous_ticket_context_in_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("CACHE_FILE", str(tmp_path / "cache.json"))
    sm = SessionManager(str(tmp_path / "state.json"))
    client = LLMClient()
    wa = WorkAssistant(jira_client=None, llm_client=client, session_manager=sm)

    first = make_ticket("T1", "First ticket")
    second = make_ticket("T2", "Second ticket")
    wa.current_tickets = [first, second]

    # simulate prior discussion
    sm.record_ticket(first)

    captured = {}

    def fake_create(model, messages, temperature):
        captured["prompt"] = messages[0]["content"]
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))])

    monkeypatch.setattr("core.llm_client.openai.chat.completions.create", fake_create)
    monkeypatch.setattr("core.work_assistant.Prompt.ask", lambda *a, **k: "good")

    wa._focus_on_ticket("T2")

    assert "T1: First ticket" in captured["prompt"]
