#!/usr/bin/env python
from pathlib import Path

# Print the content of the .env file
env_path = Path('/Users/nick.sanchez/projects_personal/personal-ticket-assistant/.env')
print(f"Env file exists: {env_path.exists()}")
if env_path.exists():
    print("Content of .env file:")
    with open(env_path, 'r') as f:
        print(f.read())
