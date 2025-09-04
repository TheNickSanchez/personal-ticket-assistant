import os
import json
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import asdict

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from utils.cache import Cache, SemanticCache
from clients.jira_client import JiraClient
from core.llm_client import LLMClient
from core.session_manager import SessionManager
from integrations.calendar_client import CalendarClient, CalendarEvent
from integrations.email_client import EmailClient
from integrations.slack_client import SlackClient
from integrations.github_client import GitHubClient
from core.models import Ticket, WorkloadAnalysis

console = Console()


class WorkAssistant:
    def __init__(
        self,
        jira_client: Optional[JiraClient] = None,
        llm_client: Optional[LLMClient] = None,
        session_manager: Optional[SessionManager] = None,
        calendar_client: Optional[CalendarClient] = None,
        slack_client: Optional[SlackClient] = None,
    ):
        self.session = session_manager or SessionManager()
        self.jira = jira_client or JiraClient()
        self.llm = llm_client or LLMClient(session_manager=self.session)
        self.calendar = calendar_client or CalendarClient()
        self.slack = slack_client
        self.current_tickets: List[Ticket] = []
        self.current_analysis: Optional[WorkloadAnalysis] = None
        self.current_dependencies: Dict[str, List[str]] = {}
        self.current_focus: Optional[Ticket] = None
        self.last_user_input: str = ""
        self.analysis_cache: Dict[str, WorkloadAnalysis] = {}
        self.current_ticket_hash: Optional[str] = None
        self.upcoming_events: List[CalendarEvent] = []
        self.session_cache = Cache()
        self.saved_focus_key: Optional[str] = None
        # Provide a semantic cache here as well for assistant-level caching
        self.semantic_cache = SemanticCache()
        # Email client for sending ticket updates
        self.email_client = EmailClient()
        # Default directory for generated files
        self.output_dir = os.getenv('OUTPUT_DIR', 'output')
        self._next_schedule_check = datetime.now()

    def load_state(self):
        """Load persisted session state"""
        data = self.session_cache.get("session") or {}
        self.saved_focus_key = data.get("current_focus")

    def save_state(self):
        """Persist current focus ticket"""
        self.session_cache.set("session", {"current_focus": self.current_focus.key if self.current_focus else None})
        self.session_manager = SessionManager()
        self.notes: List[str] = []

    def _calculate_ticket_hash(self, tickets: List[Ticket], events: Optional[List[CalendarEvent]] = None) -> str:
        """Create a hash representing the current ticket and calendar state"""
        ticket_part = "|".join(sorted(f"{t.key}:{t.updated.isoformat()}" for t in tickets))
        event_part = "|".join(
            sorted(
                f"{e.summary}:{e.start.isoformat()}:{e.end.isoformat()}" for e in (events or [])
            )
        )
        hash_input = ticket_part + "#" + event_part
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

        # Fetch upcoming calendar events
        self.upcoming_events = self.calendar.get_upcoming_events()

        # Record last scan time
        self.session.set_last_scan()

        # Determine ticket hash for caching (includes calendar state)
        self.current_ticket_hash = self._calculate_ticket_hash(self.current_tickets, self.upcoming_events)

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
                self.current_analysis = self.llm.analyze_workload(self.current_tickets, self.upcoming_events)
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
        clean_summary = self._clean_ai_response(analysis.summary)
        
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

        self.upcoming_events = self.calendar.get_upcoming_events()

        with console.status("[bold green]Analyzing priorities..."):
            self.current_analysis = self.llm.analyze_workload(self.current_tickets, self.upcoming_events)

        self.current_ticket_hash = self._calculate_ticket_hash(self.current_tickets, self.upcoming_events)
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
        console.print("Commands: 'view <ticket>', 'advise <ticket>', 'tickets', 'update <ticket>', 'email <ticket>', 'notify <ticket>', 'link <ticket>', 'plan <goal>', 'write <filename>', 'github-pr <ticket>', 'check', 'health', 'rescan', 'quit'")
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
                if datetime.now() >= self._next_schedule_check:
                    self._schedule_check(auto=True)
                    self._next_schedule_check = datetime.now() + timedelta(minutes=30)
                user_input = Prompt.ask("\n[bold blue]What should we tackle?[/bold blue] (press Enter for default)").strip()
                self.last_user_input = user_input.lower()
                
                if self._handle_user_input(user_input):
                    break
                    
            except KeyboardInterrupt:
                console.print("\n👋 Session ended. Good luck with your tickets!", style="yellow")
                break
            except EOFError:
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

        if input_lower.startswith('email '):
            ticket_key = user_input[6:].strip()
            self._email_ticket(ticket_key)
        if input_lower.startswith('notify '):
            ticket_key = user_input[7:].strip()
            self._notify_ticket(ticket_key)
            return False

        if input_lower in ['re analyze', 'reanalyze', 're-analyze']:
            console.print("🔁 Re-analyzing your workload...")
            self.llm.clear_cache()
            with console.status("[bold green]Analyzing priorities..."):
                self.current_analysis = self.llm.analyze_workload(self.current_tickets, self.upcoming_events)
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

        # Schedule and health checks
        if input_lower == 'check':
            self._schedule_check()
            return False
        if input_lower.startswith('plan'):
            goal = user_input[5:].strip()
            self._planning_workflow(goal)
            return False
            
        if input_lower.startswith('github-pr '):
            ticket_key = user_input[10:].strip()
            self._create_github_pr(ticket_key)
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
            console.print("Or '2'/'list' to see all your tickets, 'check' for schedule, 'health' for diagnostics")
        else:
            console.print("💡 Try: '2'/'list' to see your tickets, or 'help' for available commands")

        return False

    def _notify_ticket(self, ticket_key: str):
        """Send a Slack notification about a ticket"""
        ticket = self._find_ticket(ticket_key)
        if not ticket:
            console.print(f"❌ Couldn't find ticket '{ticket_key}'. Try 'list' to see available tickets.", style="red")
            return
        message = (
            f"*{ticket.key}* - {ticket.summary}\n"
            f"Priority: {ticket.priority} | Status: {ticket.status}\n"
            f"{os.getenv('JIRA_BASE_URL', '').rstrip('/')}/browse/{ticket.key}"
        )
        try:
            if not self.slack:
                self.slack = SlackClient()
            if self.slack.send_message(message):
                console.print("✅ Notification sent to Slack", style="green")
            else:
                console.print("⚠️ Failed to send Slack notification", style="yellow")
        except Exception as e:
            console.print(f"❌ Slack notification error: {e}", style="red")

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

    def _schedule_check(self, auto: bool = False) -> str:
        """Display upcoming events and free slots from the calendar."""
        events = self.calendar.get_upcoming_events()
        now = datetime.now()
        if not events:
            msg = "No upcoming events. Calendar is clear."
            if auto:
                console.print(f"📅 {msg}")
            else:
                console.print(Panel(msg, title="📅 Schedule", title_align="left", border_style="magenta"))
            return msg

        events = sorted(events, key=lambda e: e.start)
        next_event = events[0]
        lines = []
        if next_event.start > now:
            lines.append(f"Free until {next_event.start.strftime('%H:%M')}")
        lines.append(f"Next event {next_event.start.strftime('%H:%M')}: {next_event.summary}")
        last_end = next_event.end
        for ev in events[1:]:
            if ev.start - last_end >= timedelta(minutes=30):
                lines.append(f"Free slot {last_end.strftime('%H:%M')} - {ev.start.strftime('%H:%M')}")
                break
            last_end = max(last_end, ev.end)
        msg = "\n".join(lines)
        if auto:
            console.print(f"📅 {msg}")
        else:
            console.print(Panel(msg, title="📅 Schedule", title_align="left", border_style="magenta"))
        return msg

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

    def _clean_ai_response(self, response: str) -> str:
        """Clean AI response by removing debug tags and extra whitespace"""
        if not response:
            return ""
        
        # Remove various debug tags and their content
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<debug>.*?</debug>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<reasoning>.*?</reasoning>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove extra whitespace and empty lines
        lines = [line.strip() for line in cleaned.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        cleaned = '\n'.join(lines)
        
        return cleaned.strip()
    
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

    def _planning_workflow(self, goal: str):
        """Generate or continue an action plan, persisting steps."""
        if goal:
            # start a new plan, reset history to only this goal
            self.session.data["conversation_history"] = [f"plan {goal}"]
            self.session.save()
            steps: List[str] = []
        else:
            history = self.session.data.get("conversation_history", [])
            if history and history[-1].strip().lower() == "plan":
                history = history[:-1]
                self.session.data["conversation_history"] = history
                self.session.save()
            if not history:
                console.print("No active plan. Use 'plan <goal>' to begin.", style="yellow")
                return
            goal_line = history[0]
            goal = goal_line[5:] if goal_line.lower().startswith("plan ") else goal_line
            steps = history[1:]
        next_step = self.llm.plan(goal, steps)
        self.session.add_message(next_step)
        console.print(Panel(next_step, title="📝 Plan", border_style="cyan"))

    def _prompt_feedback(self, ticket: Ticket, context: str) -> None:
        feedback = Prompt.ask("Was this suggestion helpful?", choices=["good", "bad"])
        self.session.add_feedback(ticket.key, context, feedback)
    def _create_github_pr(self, ticket_key: str):
        """Create a GitHub branch, commit, and PR for a ticket."""
        if not ticket_key:
            console.print("❌ Please provide a ticket key.", style="red")
            return
        token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPO")
        if not token or not repo:
            console.print("❌ Missing GITHUB_TOKEN or GITHUB_REPO in environment.", style="red")
            return
        client = GitHubClient(token, repo)
        branch = ticket_key.replace(" ", "-")
        filename = self._sanitize_filename(f"{ticket_key}.txt")
        try:
            client.create_branch(branch)
            client.create_commit(branch, filename, f"Auto-generated file for {ticket_key}", f"chore: add {ticket_key}")
            pr = client.create_pull_request(branch, f"{ticket_key} work", f"Auto-generated PR for {ticket_key}")
            console.print(f"✅ Created PR: {pr.get('html_url', 'N/A')}", style="green")
        except Exception as e:
            console.print(f"❌ Failed to create PR: {e}", style="red")
    
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
            clean_suggestion = self._clean_ai_response(suggestion)
            console.print(Panel(
                Markdown(clean_suggestion), 
                title="🔬 Research Results", 
                title_align="left",
                border_style="blue"
            ))
            self._prompt_feedback(ticket, "Research this issue deeply and provide technical insights")
            return False

        if any(word in input_lower for word in ['plan', 'steps', 'action']):
            console.print(f"📋 Creating action plan for {ticket.key}...")
            plan = self.llm.suggest_action(ticket, "Create a detailed step-by-step action plan")
            clean_plan = self._clean_ai_response(plan)
            console.print(Panel(
                Markdown(clean_plan), 
                title="📋 Action Plan", 
                title_align="left",
                border_style="green"
            ))
            self._prompt_feedback(ticket, "Create a detailed step-by-step action plan")
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

        related = self.session.get_recent_ticket_summaries(exclude=ticket.key)
        self.session.record_ticket(ticket)

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

        if related:
            related_lines = "\n".join(f"{t['key']}: {t['summary']}" for t in related)
            console.print(Panel(related_lines, title="🔗 Related Tickets", border_style="magenta"))

        # Get AI suggestions
        with console.status("[bold green]Getting AI suggestions..."):
            suggestion = self.llm.suggest_action(ticket, related_tickets=related)

        clean_suggestion = self._clean_ai_response(suggestion)
        console.print(Panel(
            Markdown(clean_suggestion), 
            title="🤖 AI Suggestion", 
            title_align="left",
            border_style="green"
        ))
        self._prompt_feedback(ticket, "")
        
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

        # Clean and format the suggestion like "Your Work Analysis"
        clean_suggestion = self._clean_ai_response(suggestion)
        
        # Display using Markdown formatting like the analysis
        console.print(Panel(
            Markdown(clean_suggestion),
            title=f"🤖 How to tackle {ticket.key}",
            title_align="left",
            border_style="green"
        ))
        self._prompt_feedback(ticket, "The user specifically asked for help with this ticket")
        
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

    def _email_ticket(self, ticket_key: str):
        """Generate and send an email update about a ticket."""
        ticket = self._find_ticket(ticket_key)
        if not ticket:
            console.print(f"❌ Couldn't find ticket '{ticket_key}'", style="red")
            return

        console.print(f"\n✉️ Drafting email for {ticket.key}...")
        subject = f"Update on {ticket.key}: {ticket.summary}"
        with console.status("[bold green]Generating email content..."):
            body = self.llm.suggest_action(
                ticket,
                "Write a concise status email to stakeholders about this ticket"
            )
        try:
            self.email_client.send_email(subject, body)
            console.print("✅ Email sent!", style="green")
        except Exception as e:
            console.print(f"❌ Failed to send email: {e}", style="red")
    
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
            clean_research = self._clean_ai_response(research)
            console.print(Panel(
                Markdown(clean_research), 
                title="🔬 Research Results", 
                title_align="left",
                border_style="blue"
            ))
            self._prompt_feedback(ticket, "Research this issue deeply and provide technical insights")
        elif choice == "3":
            console.print("📋 Creating action plan...")
            plan = self.llm.suggest_action(ticket, "Create a detailed step-by-step action plan to resolve this ticket")
            clean_plan = self._clean_ai_response(plan)
            console.print(Panel(
                Markdown(clean_plan), 
                title="📋 Action Plan", 
                title_align="left",
                border_style="green"
            ))
            self._prompt_feedback(ticket, "Create a detailed step-by-step action plan to resolve this ticket")
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
• email <ticket-key> - Send an email update with AI-generated content
• notify <ticket-key> - Send ticket summary to Slack
• refresh - Re-run workload analysis
• open <ticket-key> - Print the Jira URL to open in browser
• health - Run environment and connectivity checks
• github-pr <ticket-key> - Create a GitHub branch and PR
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

    def start_session_web(self) -> Dict[str, Any]:
        """Begin a work session and return structured data for the web API."""
        self.session.reset()
        self.current_tickets = self.jira.get_my_tickets()
        self.session.update_session(self.current_tickets)
        self.current_dependencies = self.llm.analyze_dependencies(self.current_tickets)
        self.upcoming_events = self.calendar.get_upcoming_events()
        self.current_analysis = self.llm.analyze_workload(self.current_tickets, self.upcoming_events)
        self.session.set_last_scan()

        return {
            "tickets": [asdict(t) for t in self.current_tickets],
            "analysis": {
                "top_priority": asdict(self.current_analysis.top_priority) if self.current_analysis.top_priority else None,
                "priority_reasoning": self.current_analysis.priority_reasoning,
                "next_steps": self.current_analysis.next_steps,
                "can_help_with": self.current_analysis.can_help_with,
                "other_notable": [asdict(t) for t in self.current_analysis.other_notable],
                "summary": self.current_analysis.summary,
            },
        }
        
    def get_ticket_url(self, ticket_key: str) -> Dict[str, str]:
        """Get the URL to view a ticket in the Jira web interface."""
        return {"url": self.jira.get_ticket_url(ticket_key)}
