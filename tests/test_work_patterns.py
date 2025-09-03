import openai
from datetime import datetime
from core.llm_client import LLMClient
from core.models import Ticket
from core.session_manager import SessionManager


def test_work_patterns_persist(tmp_path):
    state_file = tmp_path / "state.json"
    sm1 = SessionManager(str(state_file))
    sm1.log_command("scan")
    sm1.log_command("scan")
    sm1.log_ticket_category("Bug")
    sm1.log_ticket_category("Feature")
    sm2 = SessionManager(str(state_file))
    patterns = sm2.get_work_patterns()
    assert patterns["commands"]["scan"] == 2
    assert patterns["categories"]["Bug"] == 1
    assert patterns["categories"]["Feature"] == 1


def test_prompt_uses_work_patterns(monkeypatch, tmp_path):
    state_file = tmp_path / "state.json"
    sm = SessionManager(str(state_file))
    sm.log_ticket_category("Bug")
    sm.log_ticket_category("Bug")
    sm.log_ticket_category("Feature")

    captured = {}

    class FakeResponse:
        def __init__(self, content: str = "analysis"):
            self.choices = [type("obj", (), {"message": type("msg", (), {"content": content})()})]

    def fake_create(model, messages, temperature):
        captured["prompt"] = messages[0]["content"]
        return FakeResponse("BUG-1")

    monkeypatch.setattr(openai.chat.completions, "create", fake_create)

    ticket = Ticket(
        key="BUG-1",
        summary="",
        description="",
        priority="P1",
        status="Open",
        assignee=None,
        created=datetime.now(),
        updated=datetime.now(),
        comments_count=0,
        labels=[],
        issue_type="Bug",
        raw_data={},
    )

    client = LLMClient(session_manager=sm)
    client.analyze_workload([ticket])

    assert "The user frequently works on: Bug, Feature" in captured["prompt"]
