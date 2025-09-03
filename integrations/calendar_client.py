from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import requests


@dataclass
class CalendarEvent:
    """Simple representation of a calendar event."""
    summary: str
    start: datetime
    end: datetime


class CalendarClient:
    """Lightweight Google Calendar client.

    This client uses an API key and calendar ID provided via environment
    variables to fetch upcoming events. If credentials are missing or an
    error occurs, it returns an empty list so callers can gracefully handle
    the absence of calendar data.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("GOOGLE_CALENDAR_API_KEY")
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    def get_upcoming_events(self, max_results: int = 10) -> List[CalendarEvent]:
        if not self.api_key:
            return []
        url = f"https://www.googleapis.com/calendar/v3/calendars/{self.calendar_id}/events"
        params = {
            "key": self.api_key,
            "timeMin": datetime.utcnow().isoformat() + "Z",
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": max_results,
        }
        try:
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            events: List[CalendarEvent] = []
            for item in data.get("items", []):
                start_raw = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
                end_raw = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")
                if not (start_raw and end_raw):
                    continue
                start = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_raw.replace("Z", "+00:00"))
                events.append(CalendarEvent(summary=item.get("summary", "Busy"), start=start, end=end))
            return events
        except Exception:
            return []
