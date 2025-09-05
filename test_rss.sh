#!/bin/bash

# This script checks if the RSS processor is working correctly

# Load environment variables if .env exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Set required environment variables for testing if not already set
if [ -z "$JIRA_RSS_URL" ]; then
  export JIRA_RSS_URL="https://docusign.atlassian.net/activity?maxResults=10&streams=account-id+IS+712020%3A48326022-8380-46d3-9945-56436ac46b3d&issues=activity+IS+comment%3Apost&os_authType=basic&title=Nick%20Activity"
fi

if [ -z "$JIRA_RSS_USERNAME" ]; then
  echo "Please set JIRA_RSS_USERNAME in your .env file or export it now"
  exit 1
fi

if [ -z "$JIRA_RSS_PASSWORD" ]; then
  echo "Please set JIRA_RSS_PASSWORD in your .env file or export it now"
  exit 1
fi

# Create a simple test script
cat > rss_test.py <<EOL
import os
import logging
from core.rss_processor import JiraRSSProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize the RSS processor
processor = JiraRSSProcessor(db_path="test_activity_metrics.db")

# Fetch and parse the RSS feed
print("Fetching RSS feed...")
activities = processor.fetch_and_parse()
print(f"Found {len(activities)} activities")

# Display the first few activities
if activities:
    print("\nSample activities:")
    for i, activity in enumerate(activities[:3]):
        print(f"\nActivity {i+1}:")
        print(f"  Ticket: {activity['ticket_id']}")
        print(f"  Type: {activity['activity_type']}")
        print(f"  Author: {activity['author']}")
        print(f"  Timestamp: {activity['timestamp']}")
        print(f"  User active: {activity['user_active']}")

    # Update the activity metrics
    print("\nUpdating activity metrics...")
    processor.update_activity_metrics(activities)
    
    # Get and display activity data for the first ticket
    first_ticket = activities[0]['ticket_id']
    print(f"\nActivity data for ticket {first_ticket}:")
    activity_data = processor.get_activity_data(first_ticket)
    for key, value in activity_data.items():
        print(f"  {key}: {value}")
    
    # Generate contextual reasoning
    print("\nGenerating contextual reasoning:")
    from core.rss_processor import generate_contextual_reasoning
    ticket_data = {
        'key': first_ticket,
        'priority': 'P1',
        'status': 'In Progress',
        'age': 30,
        'summary': 'Test ticket'
    }
    reasoning = generate_contextual_reasoning(ticket_data, activity_data)
    print(f"  {reasoning}")
else:
    print("No activities found. Check your RSS feed URL and credentials.")
EOL

# Run the test script
echo "Running RSS processor test..."
python rss_test.py

# Clean up
rm rss_test.py
