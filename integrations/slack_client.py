import os
from typing import Optional

import requests


class SlackClient:
    """Simple Slack client supporting webhook or API token."""

    def __init__(self, webhook_url: Optional[str] = None, api_token: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.api_token = api_token or os.getenv("SLACK_API_TOKEN")
        self.default_channel = os.getenv("SLACK_DEFAULT_CHANNEL")

        if not self.webhook_url and not self.api_token:
            raise ValueError("Slack webhook URL or API token must be provided")

    def send_message(self, message: str, channel: Optional[str] = None) -> bool:
        """Send a message via webhook or API token."""
        if self.webhook_url:
            payload = {"text": message}
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            return response.status_code == 200

        if self.api_token:
            channel = channel or self.default_channel
            if not channel:
                raise ValueError("Slack channel required when using API token")

            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            payload = {"channel": channel, "text": message}
            url = "https://slack.com/api/chat.postMessage"
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return bool(data.get("ok"))

        return False
