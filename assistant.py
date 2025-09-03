# Personal AI Ticket Assistant - Improved Version
# Fixes: AI parsing, description handling, command processing

import os
import json
import requests
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
import openai
from dotenv import load_dotenv
from cache import Cache, SemanticCache
from session_manager import SessionManager

# Load environment variables
load_dotenv()

console = Console()

# ==============================================================================
# DATA MODELS
# ==============================================================================

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

# ==============================================================================
# JIRA CLIENT
# ==============================================================================

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

# ==============================================================================
# LLM CLIENT
# ==============================================================================

class LLMClient:
    def __init__(self):
        self.provider = os.getenv('LLM_PROVIDER', 'openai')
        # Cache for per-ticket suggestions
        self.cache = Cache()
        self.semantic_cache = SemanticCache()
        

        if self.provider == 'openai':
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        elif self.provider == 'ollama':
            self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
            self.model = os.getenv('OLLAMA_MODEL', 'llama3.1')

        # Separate cache for workload analysis (file-backed)
        self.analysis_cache = Cache("analysis_cache.json")
    
        # Cache for the last workload analysis
        self._analysis_cache: Optional[WorkloadAnalysis] = None
        self._cache_time: Optional[datetime] = None

    def clear_cache(self):
        """Clear the stored analysis cache."""
        self._analysis_cache = None
        self._cache_time = None
        self.analysis_cache.clear()

    def analyze_workload(self, tickets: List[Ticket]) -> WorkloadAnalysis:
        """Return cached workload analysis when valid."""

        if (
            self._analysis_cache
            and self._cache_time
            and datetime.now() - self._cache_time < timedelta(hours=24)
        ):
            return self._analysis_cache

        analysis = self._compute_analysis(tickets)
        self._analysis_cache = analysis
        self._cache_time = datetime.now()
        return analysis

    def analyze_dependencies(self, tickets: List[Ticket]) -> Dict[str, List[str]]:
        """Detect simple ticket dependencies based on cross-references."""

        dependencies: Dict[str, List[str]] = {}
        keys = [t.key for t in tickets]
        for ticket in tickets:
            text = f"{ticket.summary} {ticket.description}".lower()
            deps: List[str] = []
            for key in keys:
                if key == ticket.key:
                    continue
                if key.lower() in text:
                    deps.append(key)
            if deps:
                dependencies[ticket.key] = deps
        return dependencies

    def _compute_analysis(self, tickets: List[Ticket]) -> WorkloadAnalysis:
        """Get AI analysis of your ticket workload"""
        
        # Prepare ticket data for analysis
        ticket_summaries = []
        for ticket in tickets:
            ticket_summaries.append({
                'key': ticket.key,
                'summary': ticket.summary,
                'priority': ticket.priority,
                'status': ticket.status,
                'age_days': ticket.age_days,
                'stale_days': ticket.stale_days,
                'comments_count': ticket.comments_count,
                'labels': ticket.labels,
                'issue_type': ticket.issue_type,
                'description': ticket.description[:300] if ticket.description else "No description"
            })
        
        sorted_tickets = sorted(ticket_summaries, key=lambda t: t['key'])
        ticket_hash_source = json.dumps(sorted_tickets, sort_keys=True, default=str)
        ticket_hash = hashlib.sha256(ticket_hash_source.encode('utf-8')).hexdigest()

        # Try both caches: file key and semantic (by content)
        cached = None
        if hasattr(self.analysis_cache, 'get'):
            try:
                cached = self.analysis_cache.get(ticket_hash)
            except Exception:
                cached = None
        if not cached and hasattr(self.semantic_cache, 'get_by_content'):
            cached = self.semantic_cache.get_by_content(ticket_hash)
        if cached:
            ts = datetime.fromisoformat(cached["timestamp"])
            if datetime.now() - ts < timedelta(hours=24):
                analysis_text = cached["analysis_text"]
                recommended_ticket = None
                # Use cached top_key when available to avoid re-parsing
                cached_key = cached.get("top_key") if isinstance(cached, dict) else None
                if cached_key:
                    for t in tickets:
                        if t.key == cached_key:
                            recommended_ticket = t
                            break
                if not recommended_ticket:
                    recommended_ticket = self._extract_recommended_ticket(analysis_text, tickets)
                return self._parse_analysis(analysis_text, tickets, recommended_ticket)

        prompt = f"""You are my intelligent work assistant. I have {len(tickets)} open tickets that need attention.

My tickets:
{json.dumps(ticket_summaries, indent=2, default=str)}

Please analyze my workload and help me prioritize. Be conversational and helpful, like a smart colleague.

IMPORTANT PRIORITY RULES:
1. P1/Critical tickets should almost always take priority over P3/Low priority tickets
2. "In Progress" tickets often need attention to keep momentum
3. Very old tickets (300+ days) are likely not urgent unless they're high priority
4. Look for security issues, failures, or blocking problems regardless of formal priority
5. Consider both formal priority AND actual business impact

Your analysis should identify:
1. Which ticket should be my TOP PRIORITY and why (give the exact ticket key)
2. What the next concrete steps should be for that ticket
3. Specific ways you can help me tackle it
4. Brief mention of 2-3 other notable tickets

Be specific about WHY something is urgent and WHAT we should do about it. Look for:
- P1/Critical items that need immediate attention
- Security issues or failures
- Items "In Progress" that might be stuck
- Items with customer impact (VOC_Feedback labels)
- Automation failures or blocked deployments

Respond in a conversational tone as if talking directly to me. Focus on actionable insights."""

        try:
            if self.provider == 'openai':
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                analysis_text = response.choices[0].message.content
            else:  # ollama
                response = requests.post(f"{self.ollama_host}/api/generate", json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                })
                analysis_text = response.json()["response"]
            # cache minimal analysis in file-backed cache
            # Extract the recommended ticket key from AI response
            recommended_ticket = self._extract_recommended_ticket(analysis_text, tickets)

            # cache minimal analysis in file-backed cache including recommended key
            try:
                self.analysis_cache.set(ticket_hash, {
                    "analysis_text": analysis_text,
                    "top_key": recommended_ticket.key if recommended_ticket else None,
                    "timestamp": datetime.now().isoformat(),
                })
            except Exception:
                pass
            try:
                self.semantic_cache.set_by_content({
                    "analysis_text": analysis_text,
                    "top_key": recommended_ticket.key if recommended_ticket else None,
                }, ticket_hash)
            except Exception:
                pass

            return self._parse_analysis(analysis_text, tickets, recommended_ticket)
            
        except Exception as e:
            console.print(f"❌ Error getting AI analysis: {e}", style="red")
            return self._fallback_analysis(tickets)
    
    def _extract_recommended_ticket(self, analysis_text: str, tickets: List[Ticket]) -> Optional[Ticket]:
        """Extract the ticket key that AI recommended as top priority"""
        # Look for ticket patterns in the analysis
        ticket_keys = [ticket.key for ticket in tickets]
        
        for key in ticket_keys:
            if key.upper() in analysis_text.upper():
                # Find the ticket object
                for ticket in tickets:
                    if ticket.key.upper() == key.upper():
                        return ticket
        
        # Fallback to first ticket if no clear recommendation
        return tickets[0] if tickets else None
    
    def _parse_analysis(self, analysis_text: str, tickets: List[Ticket], recommended_ticket: Optional[Ticket]) -> WorkloadAnalysis:
        """Parse AI response into structured analysis"""
        
        if not recommended_ticket:
            recommended_ticket = tickets[0] if tickets else None
        
        # Extract reasoning (simple approach - look for "why" sections)
        reasoning_match = re.search(r'why[^.]*[.!]', analysis_text, re.IGNORECASE)
        reasoning = reasoning_match.group(0) if reasoning_match else "AI analysis suggests this needs immediate attention"
        
        return WorkloadAnalysis(
            top_priority=recommended_ticket,
            priority_reasoning=reasoning,
            next_steps=["Review ticket details", "Plan approach", "Execute solution"],
            can_help_with=["Research the issue", "Create action plan", "Draft status update"],
            other_notable=tickets[1:4] if len(tickets) > 1 else [],
            summary=analysis_text
        )
    
    def _fallback_analysis(self, tickets: List[Ticket]) -> WorkloadAnalysis:
        """Simple fallback when AI isn't available"""
        if not tickets:
            return WorkloadAnalysis(
                top_priority=None,
                priority_reasoning="No tickets found",
                next_steps=[],
                can_help_with=[],
                other_notable=[],
                summary="No open tickets to analyze."
            )
        
        # Prioritize by: P1 > security/failure keywords > staleness > age
        def ticket_urgency_score(ticket: Ticket) -> tuple:
            priority = (ticket.priority or "").strip().lower()
            priority_score = {
                'p0': -1,
                'p1': 0,
                'p1 - critical': 0,
                'critical': 0,
                'highest': 0,
                'high': 1,
                'p2': 2,
                'medium': 3,
                'p3': 4,
                'low': 5,
            }.get(priority, 6)

            # Security/failure keywords boost
            keywords = ['security', 'failure', 'critical', 'blocked', 'urgent', 'voc_feedback']
            keyword_boost = 0
            for keyword in keywords:
                if keyword in ticket.summary.lower() or keyword in ticket.description.lower():
                    keyword_boost -= 2
                    break

            return (priority_score + keyword_boost, -ticket.stale_days, -ticket.age_days)
        
        p0_tickets = [t for t in tickets if t.priority.strip().upper().startswith("P0")]
        p1_tickets = [t for t in tickets if t.priority.strip().upper().startswith("P1")]
        if p0_tickets:
            top = sorted(p0_tickets, key=lambda t: (-t.stale_days, -t.age_days))[0]
            sorted_tickets = sorted(tickets, key=ticket_urgency_score)
        elif p1_tickets:
            top = sorted(p1_tickets, key=lambda t: (-t.stale_days, -t.age_days))[0]
        sorted_tickets = sorted(tickets, key=ticket_urgency_score)
        top = sorted_tickets[0]
        p0_tickets = [t for t in tickets if (t.priority or "").strip().upper().startswith("P0")]
        if p0_tickets:

            sorted_tickets = sorted(tickets, key=ticket_urgency_score)
            top = sorted(p0_tickets, key=lambda t: (-t.stale_days, -t.age_days))[0]
        else:
            p1_tickets = [t for t in tickets if (t.priority or "").strip().upper().startswith("P1")]
            if p1_tickets:
                sorted_tickets = sorted(tickets, key=ticket_urgency_score)
                top = sorted(p1_tickets, key=lambda t: (-t.stale_days, -t.age_days))[0]
            else:
                sorted_tickets = sorted(tickets, key=ticket_urgency_score)
                top = sorted_tickets[0]
        sorted_tickets = sorted(tickets, key=ticket_urgency_score)
        top = sorted_tickets[0]


        # Generate reasoning
        reasons = []
        norm_priority = (top.priority or "").strip().lower()
        if norm_priority in ['p0', 'p1', 'p1 - critical', 'critical', 'highest', 'high']:
            reasons.append(f"{top.priority.strip()} priority")
        if top.priority.startswith("P1"):
            reasons.append("P1 priority")
        elif top.priority in ['Critical', 'High']:
            reasons.append(f"{top.priority} priority")
        if top.stale_days > 30:
            reasons.append(f"stale for {top.stale_days} days")
        if 'failure' in top.summary.lower():
            reasons.append("contains failure indication")
        if 'security' in top.summary.lower() or 'security' in top.description.lower():
            reasons.append("security-related")
        
        reasoning = f"Selected due to: {', '.join(reasons)}" if reasons else f"Highest priority ticket in queue"
        
        return WorkloadAnalysis(
            top_priority=top,
            priority_reasoning=reasoning,
            next_steps=["Review ticket details", "Identify blockers", "Plan next action"],
            can_help_with=["Analyze the issue", "Suggest approach", "Draft updates"],
            other_notable=sorted_tickets[1:4],
            summary=f"You have {len(tickets)} tickets. Focus on {top.key} first - {reasoning}."
        )
    
    def suggest_action(self, ticket: Ticket, context: str = "", force_refresh: bool = False) -> str:
        """Get AI suggestion for specific ticket action"""
        cache_key = f"{ticket.key}:{context.strip()}"
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached:
                ts = datetime.fromisoformat(cached.get("timestamp"))
                if datetime.now() - ts < timedelta(hours=24):
                    return cached.get("suggestion", "")

        prompt = f"""I need help with this Jira ticket:

Ticket: {ticket.key} - {ticket.summary}
Priority: {ticket.priority} | Status: {ticket.status}
Age: {ticket.age_days} days | Stale: {ticket.stale_days} days
Comments: {ticket.comments_count} | Type: {ticket.issue_type}
Labels: {ticket.labels}

Description: {ticket.description}

Context: {context}

As my work assistant, suggest the most logical next step to move this ticket forward.
Be specific and actionable. If there are files to download, configs to check, or people to contact, mention them.
Offer concrete help with execution.

Keep response conversational and focused on getting this done."""

        try:
            if self.provider == 'openai':
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                suggestion = response.choices[0].message.content
            else:  # ollama
                response = requests.post(f"{self.ollama_host}/api/generate", json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                })
                suggestion = response.json()["response"]

        except Exception:
            suggestion = self._generate_fallback_suggestion(ticket)

        self.cache.set(cache_key, {"timestamp": datetime.now().isoformat(), "suggestion": suggestion})
        return suggestion
    
    def _generate_fallback_suggestion(self, ticket: Ticket) -> str:
        """Generate a helpful suggestion when AI is unavailable"""
        suggestions = []
        
        # Check for common patterns
        if 'update' in ticket.summary.lower():
            suggestions.append(f"This looks like an update task. Check if the new version is available and download any necessary files.")
        
        if 'failure' in ticket.summary.lower():
            suggestions.append(f"This appears to be a failure investigation. Review logs and error messages to identify the root cause.")
        
        if ticket.stale_days > 60:
            suggestions.append(f"This ticket has been stale for {ticket.stale_days} days. Consider reviewing the current status and identifying any blockers.")
        
        if ticket.comments_count == 0:
            suggestions.append("No comments yet - consider adding a status update to document your investigation or next steps.")
        
        if not suggestions:
            suggestions.append("Review the ticket details and identify the most logical next step to move this forward.")
        
        base_suggestion = " ".join(suggestions)

        return f"{base_suggestion}\n\nI can help you:\n• Break down the task into steps\n• Draft status updates\n• Research related issues\n\nWhat would be most helpful?"

    def generate_text(self, prompt: str) -> str:
        """Generate arbitrary text from a prompt."""
        try:
            if self.provider == 'openai':
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                return response.choices[0].message.content
            else:
                response = requests.post(
                    f"{self.ollama_host}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False}
                )
                return response.json()["response"]
        except Exception as e:
            return f"Error generating content: {e}"

# ==============================================================================
# WORK ASSISTANT (Main Orchestrator)
# ==============================================================================

class WorkAssistant:
    def __init__(self, jira_client: Optional[JiraClient] = None, llm_client: Optional[LLMClient] = None, session_manager: Optional[SessionManager] = None):
        self.session = session_manager or SessionManager()
        self.jira = jira_client or JiraClient()
        self.llm = llm_client or LLMClient()
        self.current_tickets: List[Ticket] = []
        self.current_analysis: Optional[WorkloadAnalysis] = None
        self.current_dependencies: Dict[str, List[str]] = {}
        self.current_focus: Optional[Ticket] = None
        self.last_user_input: str = ""
        self.analysis_cache: Dict[str, WorkloadAnalysis] = {}
        self.current_ticket_hash: Optional[str] = None
        self.session_cache = Cache()
        self.saved_focus_key: Optional[str] = None
        # Provide a semantic cache here as well for assistant-level caching
        self.semantic_cache = SemanticCache()
        # Default directory for generated files
        self.output_dir = os.getenv('OUTPUT_DIR', 'output')

    def load_state(self):
        """Load persisted session state"""
        data = self.session_cache.get("session") or {}
        self.saved_focus_key = data.get("current_focus")

    def save_state(self):
        """Persist current focus ticket"""
        self.session_cache.set("session", {"current_focus": self.current_focus.key if self.current_focus else None})
        self.session_manager = SessionManager()
        self.notes: List[str] = []

    def _calculate_ticket_hash(self, tickets: List[Ticket]) -> str:
        """Create a hash representing the current ticket set"""
        hash_input = "|".join(sorted(f"{t.key}:{t.updated.isoformat()}" for t in tickets))
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def _ticket_from_dict(self, data: Dict[str, Any]) -> Ticket:
        return Ticket(
            key=data['key'],
            summary=data['summary'],
            description=data['description'],
            priority=data['priority'],
            status=data['status'],
            assignee=data.get('assignee'),
            created=datetime.fromisoformat(data['created']),
            updated=datetime.fromisoformat(data['updated']),
            comments_count=data.get('comments_count', 0),
            labels=data.get('labels', []),
            issue_type=data.get('issue_type', ''),
            raw_data=data.get('raw_data', {}),
        )

    def start_session(self, resume: bool = False):
        """Begin a work session"""
        console.print("\n🎯 Personal AI Work Assistant", style="bold blue")
        console.print("Let me analyze your current workload...\n")

        # Determine if we should resume previous session
        resume = False
        if self.session.within_24_hours() and self.session.get_current_focus():
            last = self.session.last_scan.strftime("%Y-%m-%d %H:%M") if self.session.last_scan else "recently"
            resume = Confirm.ask(
                f"Resume previous session from {last}?",
                default=True,
            )
        if not resume:
            # Start a clean session
            self.session.reset()

        # Fetch tickets (single fetch path)
        use_cache = False
        if self.session.last_scan:
            if self.session.needs_rescan():
                if not Confirm.ask("Last scan was over 24h ago. Scan again?"):
                    self.current_tickets = [self._ticket_from_dict(t) for t in self.session.get_tickets()]
                    use_cache = True
            else:
                summary = self.session.get_ticket_summary()
                if Confirm.ask(f"{summary}\nResume last session?"):
                    self.current_tickets = [self._ticket_from_dict(t) for t in self.session.get_tickets()]
                    use_cache = True

        if not use_cache:
            with console.status("[bold green]Fetching your tickets..."):
                self.current_tickets = self.jira.get_my_tickets()
            self.session.update_session(self.current_tickets)

        if not use_cache:
            deps = self.llm.analyze_dependencies(self.current_tickets)
            self.session.set_dependencies(deps)
        else:
            deps = self.session.get_dependencies()
            if not deps:
                deps = self.llm.analyze_dependencies(self.current_tickets)
                self.session.set_dependencies(deps)
        self.current_dependencies = deps

        if not self.current_tickets:
            console.print("No open tickets found. Time to take a break! ☕", style="green")
            return

        # Record last scan time
        self.session.set_last_scan()

        # Determine ticket hash for caching
        self.current_ticket_hash = self._calculate_ticket_hash(self.current_tickets)

        # Try to load cached analysis summary
        cached = None
        try:
            cached = self.analysis_cache.get(self.current_ticket_hash)
        except Exception:
            cached = None
        if not cached:
            try:
                cached = self.semantic_cache.get_by_content(self.current_ticket_hash)
            except Exception:
                cached = None
        if cached and isinstance(cached, dict) and cached.get("summary"):
            # Determine top ticket from cached key when available
            top_ticket = None
            top_key = cached.get("top_key")
            if top_key:
                for t in self.current_tickets:
                    if t.key == top_key:
                        top_ticket = t
                        break
            if not top_ticket and self.current_tickets:
                top_ticket = self.current_tickets[0]

            self.current_analysis = WorkloadAnalysis(
                top_priority=top_ticket,
                priority_reasoning="Cached analysis",
                next_steps=["Review ticket details", "Plan approach", "Execute solution"],
                can_help_with=["Research the issue", "Create action plan", "Draft status update"],
                other_notable=self.current_tickets[1:4] if len(self.current_tickets) > 1 else [],
                summary=cached["summary"],
            )
        else:
            with console.status("[bold green]Analyzing priorities..."):
                self.current_analysis = self.llm.analyze_workload(self.current_tickets)
            # Store in both caches
            cache_payload = {
                "summary": self.current_analysis.summary,
                "top_key": self.current_analysis.top_priority.key if self.current_analysis.top_priority else None,
            }
            if hasattr(self.analysis_cache, 'set'):
                try:
                    self.analysis_cache.set(self.current_ticket_hash, cache_payload)
                except Exception:
                    pass
            else:
                self.analysis_cache[self.current_ticket_hash] = cache_payload
            if hasattr(self.semantic_cache, 'set_by_content'):
                try:
                    self.semantic_cache.set_by_content(cache_payload, self.current_ticket_hash)
                except Exception:
                    pass

        # Display the analysis once
        self._display_analysis()
        self._display_dependencies()

        # If resuming, optionally focus on last ticket
        if resume and self.session.get_current_focus():
            self._focus_on_ticket(self.session.get_current_focus())

        if resume and self.saved_focus_key:
            self._focus_on_ticket(self.saved_focus_key)

        # Start interactive session
        self._interactive_session()

    def fresh_scan(self):
        """Force ticket retrieval and fresh analysis"""
        self.llm.clear_cache()
        self.analysis_cache = {}
        self.current_focus = None
        self.saved_focus_key = None
        self.save_state()
        self.start_session()

    def _display_analysis(self):
        """Display the AI workload analysis"""
        if not self.current_analysis:
            return
            
        analysis = self.current_analysis
        
        # Clean up the analysis text (remove any debug tags)
        clean_summary = re.sub(r'<think>.*?</think>', '', analysis.summary, flags=re.DOTALL)
        clean_summary = clean_summary.strip()
        
        # Main analysis panel
        console.print(Panel(
            Markdown(clean_summary),
            title="🎯 Your Work Analysis",
            title_align="left",
            border_style="blue"
        ))
        
        if analysis.top_priority:
            # Top priority ticket details
            ticket = analysis.top_priority
            priority_text = f"""🚨 {ticket.key} - {ticket.summary}

Priority: {ticket.priority} | Status: {ticket.status} | Age: {ticket.age_days} days
Comments: {ticket.comments_count} | Type: {ticket.issue_type}
Labels: {', '.join(ticket.labels) if ticket.labels else 'None'}

Why it's urgent: {analysis.priority_reasoning}"""
            
            console.print(Panel(
                Markdown(priority_text.strip()),
                title="🎯 TOP PRIORITY",
                title_align="left",
                border_style="red"
            ))
        
        # Show what the assistant can help with
        if analysis.can_help_with:
            help_text = "\n".join(f"• {item}" for item in analysis.can_help_with)
            console.print(Panel(
                help_text,
                title="🤖 How I Can Help",
                title_align="left",
                border_style="green"
            ))

    def _display_dependencies(self):
        """Display detected ticket dependencies."""
        if not self.current_dependencies:
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Ticket")
        table.add_column("Depends On")
        for key, deps in self.current_dependencies.items():
            table.add_row(key, ", ".join(deps))
        console.print(Panel(table, title="🔗 Dependencies", border_style="magenta"))

    def _refresh_analysis(self):
        """Clear cached analysis and recompute"""
        # Clear caches
        try:
            if self.current_ticket_hash and hasattr(self.analysis_cache, 'get'):
                self.analysis_cache.set(self.current_ticket_hash, {})
        except Exception:
            pass
        try:
            self.semantic_cache.clear()
        except Exception:
            pass

        self.llm.clear_cache()

        console.print("\n🔄 Refreshing workload analysis...")
        self.llm.clear_cache()

        with console.status("[bold green]Fetching your tickets..."):
            self.current_tickets = self.jira.get_my_tickets()
        self.session.update_session(self.current_tickets)
        deps = self.llm.analyze_dependencies(self.current_tickets)
        self.session.set_dependencies(deps)
        self.current_dependencies = deps

        with console.status("[bold green]Analyzing priorities..."):
            self.current_analysis = self.llm.analyze_workload(self.current_tickets)

        self.current_ticket_hash = self._calculate_ticket_hash(self.current_tickets)
        try:
            self.analysis_cache.set(self.current_ticket_hash, {"summary": self.current_analysis.summary})
        except Exception:
            pass
        try:
            self.semantic_cache.set_by_content({"summary": self.current_analysis.summary}, self.current_ticket_hash)
        except Exception:
            pass

        self._display_analysis()
        self._display_dependencies()

    def _interactive_session(self):
        """Handle interactive conversation with the user"""
        console.print("\n" + "="*60)
        console.print("💬 Let's work together! What would you like to do?")
        console.print("Commands: 'view <ticket>', 'advise <ticket>', 'tickets', 'update <ticket>', 'link <ticket>', 'write <filename>', 'check', 'rescan', 'quit'")
        console.print("\nQuick picks:")
        top_key = self.current_analysis.top_priority.key if (self.current_analysis and self.current_analysis.top_priority) else None
        if top_key:
            console.print(f"  1) View top priority ({top_key})  [default]")
            console.print("  2) Show tickets")
            console.print(f"  3) Advise on top priority ({top_key})")
            console.print("  4) Choose a ticket by key")
            console.print("  5) Quit")
        else:
            console.print("  2) Show tickets  [default]")
            console.print("  4) Choose a ticket by key")
            console.print("  5) Quit")
        console.print("="*60 + "\n")
        
        while True:
            try:
                user_input = Prompt.ask("\n[bold blue]What should we tackle?[/bold blue] (press Enter for default)").strip()
                self.last_user_input = user_input.lower()
                
                if self._handle_user_input(user_input):
                    break
                    
            except KeyboardInterrupt:
                console.print("\n👋 Session ended. Good luck with your tickets!", style="yellow")
                break
            except Exception as e:
                console.print(f"❌ Something went wrong: {e}", style="red")
    
    def _handle_user_input(self, user_input: str) -> bool:
        """Handle various user inputs with improved parsing"""
        input_lower = user_input.lower().strip()
        if user_input:
            self.session.add_message(user_input)
        
        # Empty input = default action
        if input_lower == "":
            if self.current_analysis and self.current_analysis.top_priority:
                console.print(f"👍 Focusing on top priority: {self.current_analysis.top_priority.key}")
                self._focus_on_ticket(self.current_analysis.top_priority.key)
                return False
            else:
                self._list_tickets()
                return False
        
        # Quit commands
        if input_lower in ['quit', 'exit', 'q', 'bye']:
            if Confirm.ask("Save progress before exiting?"):
                self.session_manager.save_progress(self.current_focus, self.notes)
                console.print("💾 Progress saved.", style="green")
            console.print("👋 Great work session! See you later.", style="green")
            return True
        
        # Help commands
        if input_lower in ['help', '?', 'commands']:
            self._show_help()
            return False
        
        # List command
        if input_lower in ['list','tickets','2']:
            self._list_tickets()
            return False

        # Refresh analysis
        if input_lower in ['refresh','rescan']:
            self._refresh_analysis()
            return False

        # Smart command parsing
        if input_lower.startswith('focus ') or input_lower.startswith('view '):
            ticket_key = user_input[6:].strip()
            self._focus_on_ticket(ticket_key)
            return False
        # Numeric shortcut: 1 = focus top
        if input_lower == '1':
            if self.current_analysis and self.current_analysis.top_priority:
                self._focus_on_ticket(self.current_analysis.top_priority.key)
            else:
                console.print("No top priority ticket available.", style="yellow")
            return False
        
        if input_lower.startswith('help ') or input_lower.startswith('advise '):
            ticket_key = user_input[5:].strip()
            self._get_ticket_help(ticket_key)
            return False
        # Numeric shortcut: 3 = help top
        if input_lower == '3':
            if self.current_analysis and self.current_analysis.top_priority:
                self._get_ticket_help(self.current_analysis.top_priority.key)
            else:
                console.print("No top priority ticket available.", style="yellow")
            return False
        
        if input_lower.startswith('comment ') or input_lower.startswith('update '):
            ticket_key = user_input[8:].strip()
            self._help_with_comment(ticket_key)
            return False

        if input_lower in ['re analyze', 'reanalyze', 're-analyze']:
            console.print("🔁 Re-analyzing your workload...")
            self.llm.clear_cache()
            with console.status("[bold green]Analyzing priorities..."):
                self.current_analysis = self.llm.analyze_workload(self.current_tickets)
            self._display_analysis()
            return False
        # Numeric shortcut: 4 = choose a ticket by key (prompt)
        if input_lower == '4':
            key = Prompt.ask("Enter ticket key (e.g., CPE-3117)").strip()
            if key:
                self._focus_on_ticket(key)
            return False

        # Open ticket in browser (prints URL)
        if input_lower.startswith('open ') or input_lower.startswith('link '):
            ticket_key = user_input[5:].strip()
            self._open_ticket(ticket_key)
            return False

        if input_lower.startswith('write '):
            filename = user_input[6:].strip()
            self._create_file(filename)
            return False

        # Health check
        if input_lower in ['health','check']:
            self._health_check()
            return False
        
        # Context-aware responses
        if self.current_focus:
            return self._handle_contextual_input(input_lower)
        
        # Smart suggestions based on input
        if any(word in input_lower for word in ['research', 'investigate', 'analyze']):
            if self.current_analysis and self.current_analysis.top_priority:
                console.print(f"🔍 Let me help you research {self.current_analysis.top_priority.key}...")
                self._get_ticket_help(self.current_analysis.top_priority.key)
                return False
        
        if any(word in input_lower for word in ['yes', 'y', 'sure', 'ok', 'okay']):
            if self.current_analysis and self.current_analysis.top_priority:
                console.print(f"👍 Great! Let's focus on {self.current_analysis.top_priority.key}")
                self._focus_on_ticket(self.current_analysis.top_priority.key)
                return False
        
        if any(word in input_lower for word in ['no', 'n', 'skip', 'next']):
            console.print("No problem! What else would you like to work on?")
            self._list_tickets()
            return False
        
        # Default response with suggestions
        if self.current_analysis and self.current_analysis.top_priority:
            top_ticket = self.current_analysis.top_priority.key
            console.print(f"💡 Try: Enter, '1', or 'focus {top_ticket}' to work on your top priority")
            console.print("Or '2'/'list' to see all your tickets, 'health' for diagnostics")
        else:
            console.print("💡 Try: '2'/'list' to see your tickets, or 'help' for available commands")

        return False

    def _open_ticket(self, ticket_key: str):
        """Print the Jira URL for a ticket, to open manually"""
        if not ticket_key:
            console.print("❌ Please provide a ticket key (e.g., 'open CPE-3117')", style="red")
            return
        base = os.getenv('JIRA_BASE_URL', '').rstrip('/')
        if not base:
            console.print("❌ Missing JIRA_BASE_URL in environment.", style="red")
            return
        url = f"{base}/browse/{ticket_key.upper()}"
        console.print(f"🔗 {url}")

    def _health_check(self):
        """Run a quick environment and connectivity check"""
        console.print("\n🩺 Running health check...")
        # Env vars
        required_vars = ['JIRA_BASE_URL', 'JIRA_EMAIL', 'JIRA_API_TOKEN']
        missing = [v for v in required_vars if not os.getenv(v)]
        if missing:
            console.print("❌ Missing environment variables:", style="red")
            for v in missing:
                console.print(f"  • {v}")
        else:
            console.print("✅ Jira environment variables present")

        # LLM provider
        provider = os.getenv('LLM_PROVIDER', 'openai')
        if provider == 'openai':
            if os.getenv('OPENAI_API_KEY'):
                console.print("✅ OpenAI configured")
            else:
                console.print("⚠️ OpenAI not configured (set OPENAI_API_KEY)", style="yellow")
        elif provider == 'ollama':
            console.print("✅ Using Ollama (ensure 'ollama serve' is running)")
        else:
            console.print(f"⚠️ Unknown LLM provider: {provider}", style="yellow")

        # Basic Jira connectivity test (non-fatal)
        try:
            url = f"{os.getenv('JIRA_BASE_URL').rstrip('/')}/rest/api/3/myself"
            auth = (os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN'))
            resp = requests.get(url, auth=auth, timeout=5)
            if resp.status_code == 200:
                console.print("✅ Jira API reachable")
            else:
                console.print(f"⚠️ Jira API responded with status {resp.status_code}", style="yellow")
        except Exception as e:
            console.print(f"⚠️ Jira connectivity check failed: {e}", style="yellow")

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a filename by stripping directories and invalid characters."""
        base = os.path.basename(name)
        return re.sub(r'[^A-Za-z0-9._-]', '_', base)

    def _create_file(self, filename: str):
        """Prompt LLM for file content and write to disk."""
        if not filename:
            console.print("❌ Please provide a filename.", style="red")
            return None
        sanitized = self._sanitize_filename(filename)
        output_dir = Path(self.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        prompt = Prompt.ask(f"What should go in {sanitized}?")
        with console.status("[bold green]Generating file content..."):
            content = self.llm.generate_text(prompt)
        file_path = output_dir / sanitized
        file_path.write_text(content)
        console.print(f"💾 Created file: {file_path}")
        return file_path
    
    def _handle_contextual_input(self, input_lower: str) -> bool:
        """Handle input when we have a current focus ticket"""
        if not self.current_focus:
            return False
        
        ticket = self.current_focus
        
        if any(word in input_lower for word in ['yes', 'y', 'sure', 'ok', 'help me']):
            self._offer_actions(ticket)
            return False
        
        if any(word in input_lower for word in ['research', 'investigate']):
            console.print(f"🔍 Let me research {ticket.key} for you...")
            suggestion = self.llm.suggest_action(ticket, "Research this issue deeply and provide technical insights")
            console.print(Panel(suggestion, title="🔬 Research Results", border_style="blue"))
            return False
        
        if any(word in input_lower for word in ['plan', 'steps', 'action']):
            console.print(f"📋 Creating action plan for {ticket.key}...")
            plan = self.llm.suggest_action(ticket, "Create a detailed step-by-step action plan")
            console.print(Panel(plan, title="📋 Action Plan", border_style="green"))
            return False
        
        if any(word in input_lower for word in ['comment', 'update', 'status']):
            self._help_with_comment(ticket.key)
            return False
        
        return False
    
    def _focus_on_ticket(self, ticket_key: str):
        """Focus on a specific ticket"""
        ticket = self._find_ticket(ticket_key)
        if not ticket:
            console.print(f"❌ Couldn't find ticket '{ticket_key}'. Try 'list' to see available tickets.", style="red")
            return

        self.current_focus = ticket
        self.session.set_current_focus(ticket.key)
        self.save_state()
        console.print(f"\n🔍 Focusing on {ticket.key}...")
        
        # Show ticket details with proper description formatting
        details = f"""Summary: {ticket.summary}
Priority: {ticket.priority} | Status: {ticket.status}
Created: {ticket.created.strftime('%Y-%m-%d')} ({ticket.age_days} days ago)
Updated: {ticket.updated.strftime('%Y-%m-%d')} ({ticket.stale_days} days ago)
Comments: {ticket.comments_count} | Type: {ticket.issue_type}
Labels: {', '.join(ticket.labels) if ticket.labels else 'None'}

Description:
{ticket.description[:500] + '...' if len(ticket.description) > 500 else ticket.description}"""
        
        console.print(Panel(details.strip(), title=f"📋 {ticket.key}", border_style="blue"))
        
        # Get AI suggestions
        with console.status("[bold green]Getting AI suggestions..."):
            suggestion = self.llm.suggest_action(ticket)
        
        console.print(Panel(suggestion, title="🤖 AI Suggestion", border_style="green"))
        
        # Ask for next action
        console.print(f"\n💡 I can help you with {ticket.key}. What would you like to do?")
        console.print("Say: 'research', 'plan', 'comment', or 'help me' for options")
    
    def _get_ticket_help(self, ticket_key: str):
        """Get specific help for a ticket"""
        ticket = self._find_ticket(ticket_key)
        if not ticket:
            console.print(f"❌ Couldn't find ticket '{ticket_key}'", style="red")
            return

        self.current_focus = ticket
        self.save_state()
        console.print(f"\n🆘 Getting help for {ticket.key}...")
        
        with console.status("[bold green]Analyzing ticket and generating help..."):
            suggestion = self.llm.suggest_action(ticket, "The user specifically asked for help with this ticket")
        
        console.print(Panel(suggestion, title=f"🤖 How to tackle {ticket.key}", border_style="green"))
        
        # Ask if they want to take action
        if Confirm.ask("\nWould you like me to help you take action on this ticket?"):
            self._offer_actions(ticket)
    
    def _help_with_comment(self, ticket_key: str):
        """Help draft and post a comment"""
        ticket = self._find_ticket(ticket_key)
        if not ticket:
            console.print(f"❌ Couldn't find ticket '{ticket_key}'", style="red")
            return
        
        console.print(f"\n💬 Let's add a comment to {ticket.key}")

        # Get comment context
        context = Prompt.ask("What's the context for this comment? (e.g., 'status update', 'investigation results', 'next steps')")

        # Persist note about progress
        self.session.add_ticket_note(ticket.key, context)
        
        # Generate comment suggestion
        comment_prompt = f"""Help me draft a professional Jira comment for this ticket:

Ticket: {ticket.key} - {ticket.summary}
Context: {context}
Current status: {ticket.status}

Write a concise, professional comment that provides value to stakeholders. 
Focus on progress, next steps, or findings based on the context provided."""
        
        with console.status("[bold green]Drafting comment..."):
            try:
                if self.llm.provider == 'openai':
                    response = openai.chat.completions.create(
                        model=self.llm.model,
                        messages=[{"role": "user", "content": comment_prompt}],
                        temperature=0.7
                    )
                    suggested_comment = response.choices[0].message.content
                else:
                    suggested_comment = f"Status update: Working on {ticket.summary}. {context}. Will provide updates as progress is made."
            except:
                suggested_comment = f"Status update: Working on {ticket.summary}. {context}. Will provide updates as progress is made."
        
        console.print(Panel(suggested_comment, title="📝 Suggested Comment", border_style="yellow"))
        
        if Confirm.ask("Should I post this comment to Jira?"):
            if self.jira.add_comment(ticket.key, suggested_comment):
                console.print("✅ Comment posted successfully!", style="green")
            else:
                console.print("❌ Failed to post comment", style="red")
    
    def _offer_actions(self, ticket: Ticket):
        """Offer specific actions for a ticket"""
        console.print(f"\nI can help you with {ticket.key} in these ways:")
        console.print("1. 📝 Draft a status update comment")
        console.print("2. 🔍 Research the issue further") 
        console.print("3. 📋 Create an action plan")
        console.print("4. 🚫 Never mind")
        
        choice = Prompt.ask("What would you like me to help with?", choices=["1", "2", "3", "4"])
        
        if choice == "1":
            self._help_with_comment(ticket.key)
        elif choice == "2":
            console.print("🔍 Let me research this issue...")
            research = self.llm.suggest_action(ticket, "Research this issue deeply and provide technical insights")
            console.print(Panel(research, title="🔬 Research Results", border_style="blue"))
        elif choice == "3":
            console.print("📋 Creating action plan...")
            plan = self.llm.suggest_action(ticket, "Create a detailed step-by-step action plan to resolve this ticket")
            console.print(Panel(plan, title="📋 Action Plan", border_style="green"))
        else:
            console.print("👍 No problem! Let me know if you need help with anything else.")
    
    def _list_tickets(self):
        """Display all tickets in a nice table"""
        table = Table(title="📋 Your Current Tickets")
        table.add_column("Key", style="cyan", width=12)
        table.add_column("Priority", style="red", width=8)
        table.add_column("Status", style="green", width=12)
        table.add_column("Age", style="yellow", width=6)
        # Rich doesn't have a builtin 'orange' style; use 'yellow3'
        table.add_column("Stale", style="yellow3", width=6)
        table.add_column("Summary", style="white")
        
        for ticket in self.current_tickets:
            # Color code by staleness
            stale_style = "red" if ticket.stale_days > 60 else "yellow3" if ticket.stale_days > 30 else "white"
            
            table.add_row(
                ticket.key,
                ticket.priority,
                ticket.status,
                f"{ticket.age_days}d",
                f"[{stale_style}]{ticket.stale_days}d[/{stale_style}]",
                ticket.summary[:80] + "..." if len(ticket.summary) > 80 else ticket.summary
            )
        
        console.print(table)
        
        # Show quick action hints
        console.print(f"\n💡 Quick actions:")
        console.print(f"• focus <key> - Get detailed analysis (e.g., 'focus {self.current_tickets[0].key}')")
        console.print(f"• help <key> - Get AI assistance (e.g., 'help {self.current_tickets[0].key}')")
    
    def _find_ticket(self, ticket_key: str) -> Optional[Ticket]:
        """Find a ticket by key (case-insensitive)"""
        for ticket in self.current_tickets:
            if ticket.key.lower() == ticket_key.lower():
                return ticket
        return None
    
    def _show_help(self):
        """Show available commands"""
        help_text = """
🎯 Available Commands:

Basic Commands:
• list - Show all your tickets in a table
• focus <ticket-key> - Get detailed analysis of a specific ticket
• help <ticket-key> - Get AI assistance and action suggestions
• comment <ticket-key> - Draft and post a comment with AI help
• refresh - Re-run workload analysis
• open <ticket-key> - Print the Jira URL to open in browser
• health - Run environment and connectivity checks
• quit - End the session

Smart Commands:
• research - Research your top priority ticket
• yes/ok - Accept suggested actions
• no/skip - Move to next option

Context-Aware:
When focused on a ticket, you can say:
• research - Deep dive into the issue
• plan - Create step-by-step action plan
• comment - Draft a status update
• help me - See all available actions

Examples:
• focus CPE-3313
• help CPE-3117
• comment CPE-2925
• open CPE-3117
• health
• research (when focused on a ticket)

The assistant understands natural language, so you can also:
• "Can you help me with the Netskope ticket?"
• "What should I work on first?"
• "Research that security issue"
"""
        console.print(Panel(help_text.strip(), title="❓ Help & Commands", border_style="cyan"))

# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

def main():
    """Main application entry point"""
    
    # Check for required environment variables
    required_vars = ['JIRA_BASE_URL', 'JIRA_EMAIL', 'JIRA_API_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        console.print("❌ Missing required environment variables:", style="red")
        for var in missing_vars:
            console.print(f"  • {var}", style="red")
        console.print("\nPlease set these in your .env file or environment.", style="yellow")
        console.print("See README.md for setup instructions.", style="blue")
        return
    
    # Check for LLM configuration
    llm_provider = os.getenv('LLM_PROVIDER', 'openai')
    if llm_provider == 'openai' and not os.getenv('OPENAI_API_KEY'):
        console.print("⚠️  No OpenAI API key found. Set OPENAI_API_KEY in your .env file for best AI features.", style="yellow")
        console.print("The assistant will still work with basic analysis.", style="yellow")
    elif llm_provider == 'ollama':
        console.print("🤖 Using Ollama for AI features. Make sure it's running locally.", style="blue")

    try:
        assistant = WorkAssistant()
        assistant.load_state()
        if assistant.saved_focus_key:
            choice = Prompt.ask(
                f"Resume work on {assistant.saved_focus_key} or scan for new tickets?",
                choices=["resume", "scan"],
            )
            if choice == "resume":
                assistant.start_session(resume=True)
            else:
                assistant.fresh_scan()
        else:
            assistant.fresh_scan()
    except KeyboardInterrupt:
        console.print("\n👋 Session interrupted. See you later!", style="yellow")
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}", style="red")
        console.print("Please check your configuration and try again.", style="yellow")
        console.print("Run with JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN set.", style="blue")

if __name__ == "__main__":
    main()
