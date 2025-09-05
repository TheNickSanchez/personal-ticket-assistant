import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from rich.console import Console

from core.models import Ticket

console = Console()


class JiraClient:
    def __init__(self):
        self.base_url = os.getenv('JIRA_BASE_URL')
        self.email = os.getenv('JIRA_EMAIL')
        self.api_token = os.getenv('JIRA_API_TOKEN')

        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError("Missing Jira credentials in environment variables")

        self.auth = (self.email, self.api_token)
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def get_my_tickets(self, jql: Optional[str] = None) -> List[Ticket]:
        """Fetch tickets assigned to you or created by you"""
        if not jql:
            jql = f'assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC, updated DESC'

        url = f"{self.base_url}/rest/api/3/search"
        params = {
            'jql': jql,
            'maxResults': 50,
            'fields': 'summary,description,priority,status,assignee,created,updated,comment,labels,issuetype',
            'expand': 'changelog'
        }

        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            tickets = []
            for issue in data['issues']:
                tickets.append(self._parse_ticket(issue))

            console.print(f"✅ Fetched {len(tickets)} tickets from Jira")
            return tickets

        except requests.RequestException as e:
            console.print(f"❌ Error fetching tickets: {e}", style="red")
            return []

    def _parse_ticket(self, issue_data: Dict) -> Ticket:
        """Convert Jira API response to our Ticket model"""
        fields = issue_data['fields']

        # Parse dates
        created = datetime.fromisoformat(fields['created'].replace('Z', '+00:00'))
        updated = datetime.fromisoformat(fields['updated'].replace('Z', '+00:00'))

        # Get assignee
        assignee = None
        if fields.get('assignee'):
            assignee = fields['assignee']['displayName']

        # Count comments
        comments_count = fields.get('comment', {}).get('total', 0)

        # Get labels
        labels = [label for label in fields.get('labels', [])]

        # Parse description - handle both string and Atlassian Document Format
        description = self._parse_description(fields.get('description'))

        return Ticket(
            key=issue_data['key'],
            summary=fields['summary'],
            description=description,
            priority=fields.get('priority', {}).get('name', 'Unknown'),
            status=fields['status']['name'],
            assignee=assignee,
            created=created.replace(tzinfo=None),
            updated=updated.replace(tzinfo=None),
            comments_count=comments_count,
            labels=labels,
            issue_type=fields['issuetype']['name'],
            raw_data=issue_data
        )

    def _parse_description(self, description_data: Any) -> str:
        """Parse Jira description from various formats"""
        if not description_data:
            return "No description available"

        if isinstance(description_data, str):
            return description_data

        if isinstance(description_data, dict):
            # Handle Atlassian Document Format
            return self._extract_text_from_adf(description_data)

        return str(description_data)

    def _extract_text_from_adf(self, adf_doc: dict) -> str:
        """Extract plain text from Atlassian Document Format"""
        if not isinstance(adf_doc, dict):
            return str(adf_doc)

        text_parts = []

        def extract_text(node):
            if isinstance(node, dict):
                if node.get('type') == 'text':
                    text_parts.append(node.get('text', ''))
                elif 'content' in node:
                    for child in node['content']:
                        extract_text(child)
                elif node.get('type') == 'inlineCard':
                    # Extract URL from inline cards
                    url = node.get('attrs', {}).get('url', '')
                    if url:
                        text_parts.append(f"[Link: {url}]")
            elif isinstance(node, list):
                for item in node:
                    extract_text(item)

        extract_text(adf_doc)
        return ' '.join(text_parts).strip() or "No description available"

    def get_ticket_url(self, ticket_key: str) -> str:
        """Generate a URL to view a ticket in the Jira web interface"""
        return f"{self.base_url}/browse/{ticket_key}"

    def get_ticket(self, ticket_key: str) -> Optional[Ticket]:
        """Get a specific ticket by key"""
        url = f"{self.base_url}/rest/api/3/issue/{ticket_key}"
        params = {
            'fields': 'key,summary,description,priority,status,assignee,created,updated,comment,labels,issuetype'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            issue = response.json()
            return self._convert_to_ticket(issue)
        except requests.RequestException as e:
            print(f"Error fetching ticket {ticket_key}: {e}")
            return None
        
    def add_comment(self, ticket_key: str, comment: str) -> bool:
        """Add a comment to a Jira ticket"""
        url = f"{self.base_url}/rest/api/3/issue/{ticket_key}/comment"
        payload = {"body": comment}

        try:
            response = requests.post(url, auth=self.auth, headers=self.headers, json=payload)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            console.print(f"❌ Error adding comment: {e}", style="red")
            return False
