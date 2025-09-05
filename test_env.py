#!/usr/bin/env python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables with explicit path
env_path = Path('/Users/nick.sanchez/projects_personal/personal-ticket-assistant/.env')
load_dotenv(dotenv_path=env_path)

# Print Jira credentials
print("JIRA_BASE_URL:", os.getenv("JIRA_BASE_URL"))
print("JIRA_EMAIL:", os.getenv("JIRA_EMAIL"))
print("JIRA_API_TOKEN:", os.getenv("JIRA_API_TOKEN"))
print(f"Env file exists: {env_path.exists()}")
print(f"Env file path: {env_path}")
