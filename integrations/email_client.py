import os
import smtplib
from email.message import EmailMessage

class EmailClient:
    """Simple SMTP email sender using credentials from environment variables."""

    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME")
        self.password = os.getenv("SMTP_PASSWORD")
        self.from_addr = os.getenv("SMTP_FROM", self.username)
        self.default_to = os.getenv("SMTP_TO", self.username)
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    def send_email(self, subject: str, body: str, to_address: str | None = None) -> None:
        """Send an email with the given subject and body."""
        if not all([self.host, self.port, self.from_addr]):
            raise ValueError("Missing SMTP configuration")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = to_address or self.default_to
        msg.set_content(body)

        with smtplib.SMTP(self.host, self.port) as server:
            if self.use_tls:
                try:
                    server.starttls()
                except smtplib.SMTPException:
                    pass
            if self.username and self.password:
                server.login(self.username, self.password)
            server.send_message(msg)
