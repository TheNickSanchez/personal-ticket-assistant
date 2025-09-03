from datetime import datetime, timedelta

from core.session_manager import SessionManager


def test_session_persistence(tmp_path):
    state_file = tmp_path / "state.json"
    sm1 = SessionManager(str(state_file))
    sm1.set_last_scan()
    sm1.set_current_focus("ABC-123")
    sm1.add_ticket_note("ABC-123", "Investigating")
    sm1.add_message("focused on ticket")

    sm2 = SessionManager(str(state_file))
    assert sm2.get_current_focus() == "ABC-123"
    assert sm2.data["ticket_progress"]["ABC-123"] == "Investigating"
    assert sm2.within_24_hours() is True
    assert "focused on ticket" in sm2.data["conversation_history"]


def test_within_24_hours(tmp_path):
    state_file = tmp_path / "state.json"
    sm = SessionManager(str(state_file))
    sm.data["last_scan"] = (datetime.now() - timedelta(hours=25)).isoformat()
    sm.save()
    assert sm.within_24_hours() is False
    sm.data["last_scan"] = (datetime.now() - timedelta(hours=2)).isoformat()
    sm.save()
    assert sm.within_24_hours() is True
