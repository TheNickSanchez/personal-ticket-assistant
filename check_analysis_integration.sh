#!/bin/bash

# This script checks if the RSS data is being integrated into the AI analysis

# Load environment variables if .env exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Create a test script to check analysis integration
cat > check_analysis_integration.py <<EOL
import os
import logging
from core.work_assistant import WorkAssistant
from utils.scheduled_tasks import task_manager
from core.rss_processor import JiraRSSProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Start the RSS processor if not already running
if not task_manager.get_rss_processor():
    print("Starting RSS processor...")
    task_manager.start_rss_sync(db_path="activity_metrics.db")
    
# Ensure we have the RSS processor
rss_processor = task_manager.get_rss_processor()
if not rss_processor:
    print("Failed to start RSS processor")
    exit(1)

# Fetch some initial data to populate the database
print("Fetching initial RSS data...")
activities = rss_processor.fetch_and_parse()
if activities:
    print(f"Found {len(activities)} activities")
    rss_processor.update_activity_metrics(activities)
else:
    print("No activities found. Check your RSS feed URL and credentials.")
    exit(1)

# Initialize the WorkAssistant
print("\nInitializing WorkAssistant...")
try:
    assistant = WorkAssistant()
    print("WorkAssistant initialized successfully")
except Exception as e:
    print(f"Error initializing WorkAssistant: {e}")
    print("Make sure your Jira credentials are set in the .env file")
    exit(1)

# Check if the RSS processor is accessible from the WorkAssistant
print("\nChecking RSS processor integration...")
if assistant.rss_processor:
    print("✅ RSS processor is accessible from WorkAssistant")
else:
    print("❌ RSS processor is NOT accessible from WorkAssistant")

# Get a list of tickets
print("\nFetching tickets...")
try:
    assistant.start_session_web()
    tickets = assistant.current_tickets
    print(f"Found {len(tickets)} tickets")
    if not tickets:
        print("No tickets found. Check your Jira configuration.")
        exit(1)
except Exception as e:
    print(f"Error fetching tickets: {e}")
    exit(1)

# Run analysis on the tickets
print("\nAnalyzing tickets...")
try:
    analysis = assistant.llm.analyze_workload(tickets)
    print("\nAnalysis Results:")
    print(f"Top priority ticket: {analysis.top_priority.key if analysis.top_priority else 'None'}")
    print(f"Reasoning: {analysis.priority_reasoning}")
    
    # Check if the reasoning contains activity-based information
    activity_phrases = [
        "comment", "activity", "recently", "since", "day", "stale"
    ]
    
    activity_found = False
    for phrase in activity_phrases:
        if phrase in analysis.priority_reasoning.lower():
            activity_found = True
            break
    
    if activity_found:
        print("\n✅ Activity data is being used in the analysis!")
        print("The reasoning contains activity-related information.")
    else:
        print("\n❌ Activity data might not be integrated in the analysis.")
        print("The reasoning doesn't contain activity-related keywords.")
        print("This could be because:")
        print("1. The RSS processor isn't fetching data correctly")
        print("2. The tickets don't have recent activity in the RSS feed")
        print("3. The integration between the RSS data and analysis isn't working")
    
except Exception as e:
    print(f"Error analyzing tickets: {e}")
    exit(1)

# Stop the RSS processor when done
print("\nStopping RSS processor...")
task_manager.stop_rss_sync()
print("Done!")
EOL

# Run the test script
echo "Running analysis integration test..."
python check_analysis_integration.py

# Clean up
rm check_analysis_integration.py
