from datetime import datetime

from assistant import WorkAssistant, Ticket


class DummySlack:
    def __init__(self):
        self.messages = []

    def send_message(self, message, channel=None):
        self.messages.append(message)
        return True


class Dummy:
    pass


def test_notify_formats_message(monkeypatch):
    ticket = Ticket(
        key="ABC-123",
        summary="Test summary",
        description="Desc",
        priority="High",
        status="Open",
        assignee=None,
        created=datetime.now(),
        updated=datetime.now(),
        comments_count=0,
        labels=[],
        issue_type="Bug",
        raw_data={},
    )

    slack = DummySlack()
    wa = WorkAssistant(Dummy(), Dummy(), Dummy(), slack_client=slack)
    wa.current_tickets = [ticket]
    wa._notify_ticket("ABC-123")
    assert slack.messages, "No message sent"
    sent = slack.messages[0]
    assert "ABC-123" in sent
    assert "Test summary" in sent
