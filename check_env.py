#!/usr/bin/env python
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Print current working directory
print("Current directory:", os.getcwd())

# Check if .env file exists
env_path = Path(os.getcwd()) / ".env"
print(".env file exists:", env_path.exists())

# If it exists, print its content
if env_path.exists():
    print("Content of .env file:")
    with open(env_path, 'r') as f:
        print(f.read())

# Load environment variables from .env file
result = load_dotenv(dotenv_path=env_path, verbose=True)
print("load_dotenv result:", result)

# Print the environment variables
print("\nEnvironment variables:")
print("JIRA_BASE_URL:", os.environ.get("JIRA_BASE_URL"))
print("JIRA_EMAIL:", os.environ.get("JIRA_EMAIL"))
print("JIRA_API_TOKEN:", os.environ.get("JIRA_API_TOKEN"))
