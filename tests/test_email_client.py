import smtplib
from integrations.email_client import EmailClient


def test_email_formatting(monkeypatch):
    sent_messages = []

    class DummySMTP:
        def __init__(self, host, port):
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def starttls(self):
            pass

        def login(self, username, password):
            pass

        def send_message(self, msg):
            sent_messages.append(msg)

    def fake_smtp(host, port):
        assert host == "localhost"
        assert port == 1025
        return DummySMTP(host, port)

    monkeypatch.setenv("SMTP_HOST", "localhost")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("SMTP_USERNAME", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "")
    monkeypatch.setenv("SMTP_FROM", "sender@example.com")
    monkeypatch.setenv("SMTP_TO", "receiver@example.com")
    monkeypatch.setenv("SMTP_USE_TLS", "false")
    monkeypatch.setattr(smtplib, "SMTP", fake_smtp)

    client = EmailClient()
    client.send_email("Test Subject", "Hello world")

    assert len(sent_messages) == 1
    msg = sent_messages[0]
    assert msg["From"] == "sender@example.com"
    assert msg["To"] == "receiver@example.com"
    assert msg["Subject"] == "Test Subject"
    assert msg.get_content().strip() == "Hello world"
