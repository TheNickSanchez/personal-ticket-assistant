from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class Ticket:
    key: str
    summary: str
    description: str
    priority: str
    status: str
    assignee: Optional[str]
    created: datetime
    updated: datetime
    comments_count: int
    labels: List[str]
    issue_type: str
    raw_data: Dict[str, Any]

    @property
    def age_days(self) -> int:
        return (datetime.now() - self.created).days

    @property
    def stale_days(self) -> int:
        return (datetime.now() - self.updated).days


@dataclass
class WorkloadAnalysis:
    top_priority: Ticket
    priority_reasoning: str
    next_steps: List[str]
    can_help_with: List[str]
    other_notable: List[Ticket]
    summary: str
