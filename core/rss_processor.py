import os
import requests
import feedparser
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Tuple
import time
import sqlite3
import threading

logger = logging.getLogger(__name__)

class JiraRSSProcessor:
    """
    Process Jira RSS activity feeds to extract ticket activity data.
    This runs as a background job to update activity metrics periodically.
    """
    
    def __init__(self, db_path: str = "activity_metrics.db"):
        """
        Initialize the RSS processor with configuration.
        
        Args:
            db_path: Path to the SQLite database for storing activity metrics
        """
        self.rss_url = os.environ.get("JIRA_RSS_URL", "")
        self.username = os.environ.get("JIRA_RSS_USERNAME", "")
        self.password = os.environ.get("JIRA_RSS_PASSWORD", "")
        self.sync_interval = int(os.environ.get("RSS_SYNC_INTERVAL_MINUTES", "30"))
        self.db_path = db_path
        self._setup_database()
        self._thread = None
        self._stop_event = threading.Event()
    
    def _setup_database(self):
        """Create the activity_metrics table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_metrics (
            ticket_id VARCHAR(20),
            last_activity_date TIMESTAMP,
            recent_comment_count INTEGER DEFAULT 0,
            days_since_activity INTEGER DEFAULT 0,
            user_recently_active BOOLEAN DEFAULT 0,
            last_updated TIMESTAMP,
            PRIMARY KEY(ticket_id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database setup complete at {self.db_path}")
    
    def fetch_and_parse(self) -> List[Dict]:
        """
        Fetch the RSS feed and parse ticket activity data.
        
        Returns:
            List of dictionaries containing activity data for each ticket
        """
        if not self.rss_url:
            logger.error("RSS URL not configured")
            return []
        
        try:
            # Fetch RSS feed with authentication
            response = requests.get(
                self.rss_url,
                auth=(self.username, self.password),
                timeout=30
            )
            response.raise_for_status()
            
            # Parse the feed
            feed = feedparser.parse(response.text)
            
            # Process entries
            activities = []
            current_user = self.username.split('@')[0] if '@' in self.username else self.username
            
            for entry in feed.entries:
                activity = self._process_entry(entry, current_user)
                if activity:
                    activities.append(activity)
            
            logger.info(f"Processed {len(activities)} activities from RSS feed")
            return activities
            
        except requests.RequestException as e:
            logger.error(f"Error fetching RSS feed: {str(e)}")
            return []
        except Exception as e:
            logger.exception(f"Error parsing RSS feed: {str(e)}")
            return []
    
    def _process_entry(self, entry, current_user: str) -> Optional[Dict]:
        """
        Process a single RSS entry to extract ticket activity data.
        
        Args:
            entry: RSS feed entry
            current_user: Current user's username for checking activity
            
        Returns:
            Dictionary with ticket activity data or None if parsing failed
        """
        try:
            # Extract ticket ID from title
            title = entry.get('title', '')
            ticket_id = None
            
            # Look for ticket IDs like ABC-123
            import re
            ticket_match = re.search(r'([A-Z]+-\d+)', title)
            if ticket_match:
                ticket_id = ticket_match.group(1)
            
            if not ticket_id:
                return None
                
            # Extract timestamp
            published = entry.get('published_parsed')
            if published:
                timestamp = datetime(*published[:6], tzinfo=timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
            
            # Determine if current user was active
            author = entry.get('author', '')
            user_active = current_user.lower() in author.lower()
            
            # Determine activity type
            activity_type = 'comment'  # Default
            if 'updated' in title.lower():
                activity_type = 'update'
            elif 'created' in title.lower():
                activity_type = 'create'
                
            return {
                'ticket_id': ticket_id,
                'timestamp': timestamp,
                'activity_type': activity_type,
                'author': author,
                'user_active': user_active
            }
            
        except Exception as e:
            logger.error(f"Error processing entry: {str(e)}")
            return None
    
    def update_activity_metrics(self, activities: List[Dict]):
        """
        Update the activity_metrics database with new activity data.
        
        Args:
            activities: List of activity dictionaries
        """
        if not activities:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now(timezone.utc)
        
        try:
            # Group activities by ticket_id
            ticket_activities = {}
            for activity in activities:
                ticket_id = activity['ticket_id']
                if ticket_id not in ticket_activities:
                    ticket_activities[ticket_id] = []
                ticket_activities[ticket_id].append(activity)
            
            # Process each ticket's activities
            for ticket_id, ticket_acts in ticket_activities.items():
                # Sort by timestamp (newest first)
                ticket_acts.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # Get latest activity
                latest = ticket_acts[0]
                last_activity_date = latest['timestamp']
                
                # Calculate days since activity
                days_since = (now - last_activity_date).days
                
                # Count recent comments (last 7 days)
                week_ago = now.timestamp() - (7 * 24 * 60 * 60)
                recent_comments = sum(
                    1 for a in ticket_acts 
                    if a['activity_type'] == 'comment' and a['timestamp'].timestamp() > week_ago
                )
                
                # Check if user was recently active (last 14 days)
                two_weeks_ago = now.timestamp() - (14 * 24 * 60 * 60)
                user_active = any(
                    a['user_active'] for a in ticket_acts
                    if a['timestamp'].timestamp() > two_weeks_ago
                )
                
                # Update or insert metrics
                cursor.execute('''
                INSERT INTO activity_metrics 
                (ticket_id, last_activity_date, recent_comment_count, days_since_activity, user_recently_active, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticket_id) DO UPDATE SET
                    last_activity_date = ?,
                    recent_comment_count = ?,
                    days_since_activity = ?,
                    user_recently_active = ?,
                    last_updated = ?
                ''', (
                    ticket_id, last_activity_date, recent_comments, days_since, user_active, now,
                    last_activity_date, recent_comments, days_since, user_active, now
                ))
            
            conn.commit()
            logger.info(f"Updated activity metrics for {len(ticket_activities)} tickets")
            
        except Exception as e:
            conn.rollback()
            logger.exception(f"Error updating activity metrics: {str(e)}")
        finally:
            conn.close()
    
    def get_activity_data(self, ticket_id: str) -> Dict:
        """
        Get activity data for a specific ticket.
        
        Args:
            ticket_id: The Jira ticket ID
            
        Returns:
            Dictionary with activity metrics or empty dict if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT last_activity_date, recent_comment_count, days_since_activity, user_recently_active
            FROM activity_metrics
            WHERE ticket_id = ?
            ''', (ticket_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'last_activity_date': row[0],
                    'recent_comment_count': row[1],
                    'days_since_activity': row[2],
                    'user_recently_active': bool(row[3])
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching activity data for {ticket_id}: {str(e)}")
            return {}
        finally:
            conn.close()
    
    def process_and_update(self):
        """Process RSS feed and update activity metrics"""
        activities = self.fetch_and_parse()
        self.update_activity_metrics(activities)
    
    def start_background_sync(self):
        """Start background thread for periodic syncing"""
        if self._thread and self._thread.is_alive():
            logger.warning("Background sync already running")
            return
            
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._background_sync_worker, daemon=True)
        self._thread.start()
        logger.info("Started background RSS sync")
    
    def stop_background_sync(self):
        """Stop background sync thread"""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=5)
            logger.info("Stopped background RSS sync")
    
    def _background_sync_worker(self):
        """Worker function for background thread"""
        while not self._stop_event.is_set():
            try:
                self.process_and_update()
            except Exception as e:
                logger.exception(f"Error in background sync: {str(e)}")
                
            # Wait for the next interval or until stopped
            interval_seconds = self.sync_interval * 60
            for _ in range(interval_seconds):
                if self._stop_event.is_set():
                    break
                time.sleep(1)


def generate_contextual_reasoning(ticket, activity_data):
    """
    Generate contextual reasoning based on ticket and activity data.
    
    Args:
        ticket: Ticket object with standard fields
        activity_data: Activity metrics for the ticket
        
    Returns:
        String with contextual reasoning for prioritization
    """
    if not activity_data:
        return ""
        
    reasoning = ""
    
    # Extract data
    age = int(ticket.get('age', '0').replace('d', ''))
    priority = ticket.get('priority', '')
    status = ticket.get('status', '')
    days_since_activity = activity_data.get('days_since_activity', 0)
    recent_comment_count = activity_data.get('recent_comment_count', 0)
    user_recently_active = activity_data.get('user_recently_active', False)
    
    # Generate reasoning based on patterns
    if age > 180 and days_since_activity > 90:
        reasoning = f"Stale for {age} days with no activity for {days_since_activity} days - likely resolved itself or no longer relevant"
    
    elif priority == "P1" and recent_comment_count > 0:
        reasoning = f"P1 with {recent_comment_count} recent comments - check for deployment blockers or escalations"
    
    elif user_recently_active:
        reasoning = f"You were active on this recently - pick up where you left off"
    
    elif status == "In Progress" and days_since_activity > 21:
        reasoning = f"In Progress but silent for {days_since_activity} days - follow up on status or roadblocks"
    
    return reasoning
