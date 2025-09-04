import os
import re
import json
import requests
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import openai

from rich.console import Console
from utils.cache import Cache, SemanticCache
from core.session_manager import SessionManager
from core.knowledge_base import KnowledgeBase
from core.models import Ticket, WorkloadAnalysis

console = Console()


class LLMClient:
    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None, session_manager: Optional[SessionManager] = None):
        self.session = session_manager or SessionManager()
        self.provider = os.getenv('LLM_PROVIDER', 'openai')
        # Cache for per-ticket suggestions
        self.cache = Cache()
        self.semantic_cache = SemanticCache()
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.work_patterns: Dict[str, Dict[str, int]] = {}
        if self.session:
            self.work_patterns = self.session.get_work_patterns()
        

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

    def analyze_workload(self, tickets: List[Ticket], events: Optional[List[Any]] = None) -> WorkloadAnalysis:
        """Return cached workload analysis when valid."""

        if self.session:
            self.session.log_command("analyze_workload")
            for t in tickets:
                if t.issue_type:
                    self.session.log_ticket_category(t.issue_type)
            self.work_patterns = self.session.get_work_patterns()

        if (
            self._analysis_cache
            and self._cache_time
            and datetime.now() - self._cache_time < timedelta(hours=24)
        ):
            return self._analysis_cache

        analysis = self._compute_analysis(tickets, self.work_patterns)
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

    def _compute_analysis(self, tickets: List[Ticket], patterns: Optional[Dict[str, Dict[str, int]]] = None) -> WorkloadAnalysis:
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
        
        event_summaries = []

        sorted_tickets = sorted(ticket_summaries, key=lambda t: t['key'])
        state_hash_source = json.dumps({'tickets': sorted_tickets, 'events': event_summaries}, sort_keys=True, default=str)
        ticket_hash = hashlib.sha256(state_hash_source.encode('utf-8')).hexdigest()

        # Try both caches: file key and semantic (by content)
        cached = None
        if hasattr(self.analysis_cache, 'get'):
            try:
                cached = self.analysis_cache.get(ticket_hash)
            except Exception:
                cached = None
        if not cached and hasattr(self.semantic_cache, 'get_by_content'):
            cached = self.semantic_cache.get_by_content(ticket_hash)
        if cached and isinstance(cached, dict) and "timestamp" in cached:
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

        category_focus = ""
        if patterns and patterns.get("categories"):
            sorted_cats = sorted(patterns["categories"].items(), key=lambda x: x[1], reverse=True)
            cat_list = ", ".join(cat for cat, _ in sorted_cats)
            category_focus = f"\nThe user frequently works on: {cat_list}. Prioritize these categories when relevant.\n"

        prompt = f"""You are my intelligent work assistant. I have {len(tickets)} open tickets that need attention.

My tickets:
{json.dumps(ticket_summaries, indent=2, default=str)}

Upcoming calendar events:
{json.dumps(event_summaries, indent=2, default=str)}

{category_focus}
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
    
    def suggest_action(
        self,
        ticket: Ticket,
        context: str = "",
        force_refresh: bool = False,
        related_tickets: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Get AI suggestion for specific ticket action"""
        base_key = f"{ticket.key}:{context.strip()}"
        if related_tickets:
            rel_key = ",".join(sorted(t["key"] for t in related_tickets))
            cache_key = f"{base_key}:{rel_key}"
        else:
            cache_key = base_key
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached and isinstance(cached, dict) and "timestamp" in cached:
                ts = datetime.fromisoformat(cached.get("timestamp"))
                if datetime.now() - ts < timedelta(hours=24):
                    return cached.get("suggestion", "")

        similar = self.knowledge_base.search(ticket.summary)
        kb_text = ""
        if similar:
            lines = [f"- {e['summary']}: {e['resolution']}" for e in similar[:3]]
            kb_text = "\nSimilar past tickets:\n" + "\n".join(lines) + "\n"

        prompt = f"""I need help with this Jira ticket:

Ticket: {ticket.key} - {ticket.summary}
Priority: {ticket.priority} | Status: {ticket.status}
Age: {ticket.age_days} days | Stale: {ticket.stale_days} days
Comments: {ticket.comments_count} | Type: {ticket.issue_type}
Labels: {ticket.labels}

Description: {ticket.description}

Context: {context}

{kb_text}

As my work assistant, suggest the most logical next step to move this ticket forward.
Be specific and actionable. If there are files to download, configs to check, or people to contact, mention them.
Offer concrete help with execution."""

        if related_tickets:
            prompt += "Recently discussed tickets:\n"
            for rt in related_tickets:
                prompt += f"- {rt['key']}: {rt['summary']}\n"
            prompt += "\nUse these for context and reference if helpful.\n"

        prompt += (
            "As my work assistant, suggest the most logical next step to move this ticket forward.\n"
            "Be specific and actionable. If there are files to download, configs to check, or people to contact, mention them.\n"
            "Offer concrete help with execution.\n\n"
            "Keep response conversational and focused on getting this done."
        )

        past_feedback = self.session.get_feedback(ticket.key, context)
        if past_feedback:
            prompt += f"\n\nPrevious feedback: {', '.join(past_feedback)}"

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

        if similar:
            past = "\n" + kb_text.strip() if kb_text else ""
            suggestion = f"{past}\n{suggestion}".strip()
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

    def plan(self, goal: str, steps: List[str]) -> str:
        """Generate the next step in a planning sequence including prior steps."""
        history = "\n".join(steps) if steps else "None"
        prompt = (
            f"We are planning how to {goal}.\n"
            f"Steps so far:\n{history}\n"
            "Provide the next step in the plan."
        )
        return self.generate_text(prompt)

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

