import unittest
from unittest.mock import patch, MagicMock
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone

from core.rss_processor import JiraRSSProcessor, generate_contextual_reasoning


class TestJiraRSSProcessor(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        # Create processor with test database
        self.processor = JiraRSSProcessor(db_path=self.db_path)
        
        # Set up test environment variables
        os.environ['JIRA_RSS_URL'] = 'https://test.atlassian.net/activity'
        os.environ['JIRA_RSS_USERNAME'] = 'test@example.com'
        os.environ['JIRA_RSS_PASSWORD'] = 'test_token'
        
    def tearDown(self):
        # Close and remove the temporary database
        os.close(self.db_fd)
        os.unlink(self.db_path)
        
    @patch('requests.get')
    def test_fetch_and_parse(self, mock_get):
        # Mock the response from the RSS feed
        mock_response = MagicMock()
        mock_response.text = """
        <?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>TEST-123: Comment added</title>
            <author>
              <name>Test User</name>
            </author>
            <published>2023-09-01T12:00:00Z</published>
          </entry>
          <entry>
            <title>TEST-456: Updated status</title>
            <author>
              <name>test@example.com</name>
            </author>
            <published>2023-09-02T13:00:00Z</published>
          </entry>
        </feed>
        """
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Create a mock for feedparser.parse
        with patch('feedparser.parse') as mock_parse:
            # Set up the mock to return a feed with two entries
            mock_feed = MagicMock()
            mock_feed.entries = [
                {
                    'title': 'TEST-123: Comment added',
                    'author': 'Test User',
                    'published_parsed': (2023, 9, 1, 12, 0, 0, 0, 0, 0)
                },
                {
                    'title': 'TEST-456: Updated status',
                    'author': 'test@example.com',
                    'published_parsed': (2023, 9, 2, 13, 0, 0, 0, 0, 0)
                }
            ]
            mock_parse.return_value = mock_feed
            
            # Call the method
            activities = self.processor.fetch_and_parse()
            
            # Verify the results
            self.assertEqual(len(activities), 2)
            self.assertEqual(activities[0]['ticket_id'], 'TEST-123')
            self.assertEqual(activities[0]['activity_type'], 'comment')
            self.assertEqual(activities[0]['user_active'], False)
            
            self.assertEqual(activities[1]['ticket_id'], 'TEST-456')
            self.assertEqual(activities[1]['activity_type'], 'update')
            self.assertEqual(activities[1]['user_active'], True)
    
    def test_update_activity_metrics(self):
        # Create test activities
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        month_ago = now - timedelta(days=30)
        
        activities = [
            {
                'ticket_id': 'TEST-123',
                'timestamp': yesterday,
                'activity_type': 'comment',
                'author': 'Test User',
                'user_active': False
            },
            {
                'ticket_id': 'TEST-123',
                'timestamp': month_ago,
                'activity_type': 'update',
                'author': 'test@example.com',
                'user_active': True
            }
        ]
        
        # Call the method
        self.processor.update_activity_metrics(activities)
        
        # Verify the database was updated
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM activity_metrics WHERE ticket_id = ?', ('TEST-123',))
        row = cursor.fetchone()
        conn.close()
        
        # Check results
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 'TEST-123')  # ticket_id
        self.assertEqual(row[2], 1)  # recent_comment_count
        self.assertEqual(row[3], 1)  # days_since_activity
        
    def test_generate_contextual_reasoning(self):
        # Test ticket data
        ticket = {
            'key': 'TEST-123',
            'priority': 'P1',
            'status': 'In Progress',
            'age': 100,
            'summary': 'Security vulnerability'
        }
        
        # Test activity data
        activity_data = {
            'last_activity_date': '2023-09-01T12:00:00Z',
            'recent_comment_count': 5,
            'days_since_activity': 25,
            'user_recently_active': True
        }
        
        # Generate reasoning
        reasoning = generate_contextual_reasoning(ticket, activity_data)
        
        # Check that reasoning contains expected content
        self.assertIn('You were active on this recently', reasoning)


if __name__ == '__main__':
    unittest.main()
