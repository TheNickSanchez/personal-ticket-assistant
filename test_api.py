#!/usr/bin/env python
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Print the environment variables
print("JIRA_BASE_URL:", os.environ.get("JIRA_BASE_URL"))
print("JIRA_EMAIL:", os.environ.get("JIRA_EMAIL"))
print("JIRA_API_TOKEN:", os.environ.get("JIRA_API_TOKEN"))

# Try to access the API endpoint
try:
    response = requests.post("http://localhost:8002/api/session/start")
    print(f"API Response Status: {response.status_code}")
    if response.ok:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error connecting to API: {e}")

# Try to access the ticket URL endpoint for a test ticket
try:
    response = requests.get("http://localhost:8002/api/ticket/APP-123/url")
    print(f"\nTicket URL API Response Status: {response.status_code}")
    if response.ok:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error connecting to ticket URL API: {e}")
