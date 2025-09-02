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
