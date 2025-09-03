from datetime import datetime

from core.knowledge_base import KnowledgeBase
from core.session_manager import SessionManager
from assistant import LLMClient, Ticket


def test_session_manager_records_done_ticket(tmp_path):
    kb_file = tmp_path / "kb.json"
    state_file = tmp_path / "state.json"
    sm = SessionManager(str(state_file), knowledge_base_path=str(kb_file))
    ticket = Ticket(
        key="ABC-1",
        summary="Fix login bug",
        description="Restart service",
        priority="P1",
        status="In Progress",
        assignee=None,
        created=datetime.now(),
        updated=datetime.now(),
        comments_count=0,
        labels=[],
        issue_type="Bug",
        raw_data={},
    )
    sm.update_session([ticket])
    ticket.status = "Done"
    sm.update_session([ticket])
    kb = KnowledgeBase(str(kb_file))
    results = kb.search("login")
    assert any(r["ticket_key"] == "ABC-1" for r in results)


def test_llmclient_suggest_action_uses_history(tmp_path):
    kb_file = tmp_path / "kb.json"
    kb = KnowledgeBase(str(kb_file))
    kb.add("ABC-1", "Fix login bug", "Restart service")
    client = LLMClient(knowledge_base=kb)
    ticket = Ticket(
        key="ABC-2",
        summary="Fix login bug",
        description="User cannot login",
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
    suggestion = client.suggest_action(ticket, force_refresh=True)
    assert "Restart service" in suggestion
