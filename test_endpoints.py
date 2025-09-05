#!/usr/bin/env python
import requests
import json
import time

# Give the server a moment to start up
print("Waiting for server to start...")
time.sleep(2)

# Try to access the API endpoint
try:
    print("Testing session start endpoint...")
    response = requests.post("http://localhost:8003/api/session/start")
    print(f"API Response Status: {response.status_code}")
    if response.ok:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error connecting to API: {e}")

# Try to access the ticket URL endpoint for a test ticket
try:
    print("\nTesting ticket URL endpoint...")
    response = requests.get("http://localhost:8003/api/ticket/APP-123/url")
    print(f"Ticket URL API Response Status: {response.status_code}")
    if response.ok:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error connecting to ticket URL API: {e}")
