#!/bin/bash

# This script examines the activity_metrics database to check for stored RSS data

# Check if the database file exists
if [ -f "activity_metrics.db" ]; then
  echo "Found activity_metrics.db"
else
  echo "activity_metrics.db not found. Run the application first to create it."
  exit 1
fi

# Use sqlite3 to query the database
echo "Querying activity_metrics database..."
echo
echo "Table Schema:"
sqlite3 activity_metrics.db ".schema activity_metrics"
echo
echo "Row Count:"
sqlite3 activity_metrics.db "SELECT COUNT(*) FROM activity_metrics;"
echo
echo "Sample Records (up to 5):"
sqlite3 activity_metrics.db "SELECT ticket_id, datetime(last_activity_date) as last_activity, recent_comment_count, days_since_activity, user_recently_active FROM activity_metrics LIMIT 5;"
echo
echo "Most Recent Activity:"
sqlite3 activity_metrics.db "SELECT ticket_id, datetime(last_activity_date) as last_activity, recent_comment_count, days_since_activity, user_recently_active FROM activity_metrics ORDER BY last_activity_date DESC LIMIT 1;"
echo
