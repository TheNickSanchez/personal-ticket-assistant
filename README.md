# 🎯 Personal AI Ticket Assistant

Your intelligent work companion that pulls Jira tickets and helps you prioritize, understand, and tackle your daily work through conversational AI.

## Quick Start

### 1. Setup
```bash
# Clone and setup
git clone <your-repo>
cd personal-ticket-assistant
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy and edit your environment file
cp .env.example .env
# Edit .env with your actual credentials (see below)
```

### 3. Get Your Jira API Token
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token and add it to your `.env` file

### 4. Choose Your AI Provider

**Option A: OpenAI (Recommended for best results)**
- Get API key from https://platform.openai.com/api-keys
- Add to `.env`: `OPENAI_API_KEY=your_key_here`

**Option B: Local Ollama (Free, private)**
```bash
# Install Ollama from https://ollama.ai/
# Pull a model
ollama pull llama3.1
# Make sure it's running (default: http://localhost:11434)
```

### 5. Configure GitHub (optional)
1. Create a personal access token at https://github.com/settings/tokens with `repo` scope
2. Add to `.env`:
   ```bash
   GITHUB_TOKEN=ghp_your_token_here
   GITHUB_REPO=owner/repo  # e.g. myuser/myrepo
   ```

### 6. Run Your Assistant
```bash
python assistant.py
```

## Example Session

```
🎯 Personal AI Work Assistant
Let me analyze your current workload...

✅ Fetched 8 tickets from Jira

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🎯 Your Work Analysis                                                    ┃
┠──────────────────────────────────────────────────────────────────────────┨
┃                                                                          ┃
┃ Good morning! I found 8 open tickets that need your attention.          ┃
┃                                                                          ┃
┃ SEC-2847 should be your TOP PRIORITY. It's a critical authentication    ┃
┃ bypass vulnerability affecting your SSO system, reported 4 days ago     ┃
┃ with zero progress. This impacts all users and needs immediate action.  ┃
┃                                                                          ┃
┃ I can help you tackle this right now by researching the CVE, creating   ┃
┃ a remediation plan, and drafting status updates for stakeholders.       ┃
┃                                                                          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

💬 Let's work together! What would you like to do?
Commands: 'focus <ticket>', 'help <ticket>', 'list', 'comment <ticket>', 'github-pr <ticket>', 'refresh', 'quit'

What should we tackle? help SEC-2847

🆘 Getting help for SEC-2847...
[AI provides detailed analysis and action plan]

Would you like me to help you take action on this ticket? yes
I can help you with SEC-2847 in these ways:
1. 📝 Draft a status update comment
2. 🔍 Research the issue further
3. 📋 Create an action plan
```

## Commands

- `list` - Show all your tickets in a table
- `focus <ticket>` - Get detailed analysis of a specific ticket
- `help <ticket>` - Get AI suggestions and offers to help with actions
- `comment <ticket>` - Draft and post a comment with AI assistance
- `github-pr <ticket>` - Create a GitHub branch and pull request
- `refresh` - Re-run workload analysis
- `quit` - End your work session

## Configuration Details

### Required Environment Variables
```bash
# Your Jira instance URL (no trailing slash)
JIRA_BASE_URL=https://yourcompany.atlassian.net

# Your Jira email address
JIRA_EMAIL=your.email@company.com  

# Your Jira API token (not your password!)
JIRA_API_TOKEN=ATATT3xFfGF0...your_token_here
```

### AI Provider Options

**OpenAI (Best results)**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...your_key_here
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo for faster/cheaper
```

**Ollama (Free, runs locally)**
```bash
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1  # or codestral, mistral, etc.
```

### GitHub Integration (optional)
```bash
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=owner/repo  # e.g. myuser/myrepo
```

## Customization

### Custom JQL Query
By default, the assistant fetches tickets assigned to you. You can customize this by modifying the JQL in the `get_my_tickets()` method:

```python
# In JiraClient.get_my_tickets(), change this line:
jql = f'assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC, updated DESC'

# Examples:
# All tickets in your project: 'project = MYPROJ AND statusCategory != Done'
# Tickets you reported: 'reporter = currentUser() AND statusCategory != Done'  
# Specific component: 'component = "Security" AND statusCategory != Done'
```

### Adding Your Own Logic
The assistant is designed to be easily extensible. Key areas to customize:

1. **Priority Logic**: Modify `_fallback_analysis()` for custom prioritization
2. **AI Prompts**: Update prompts in `analyze_workload()` and `suggest_action()`
3. **Actions**: Add new commands in `_interactive_session()`

## Troubleshooting

### Common Issues

**"Missing required environment variables"**
- Make sure your `.env` file exists and has all required Jira settings
- Check that your `.env` file is in the same directory as `assistant.py`

**"Error fetching tickets"**
- Verify your Jira URL (should include https://, no trailing slash)
- Check your API token is correct (not your password)
- Test your credentials by visiting: `https://yourcompany.atlassian.net/rest/api/3/myself`

**"Error getting AI analysis"**
- For OpenAI: Check your API key and that you have credits
- For Ollama: Ensure Ollama is running (`ollama serve`) and model is pulled
- The assistant will fall back to basic analysis if AI fails

**"No open tickets found"**
- Check that you have tickets assigned to you in Jira
- Try customizing the JQL query (see Customization section)
- Use `list` command to see what tickets were fetched

### Getting Jira API Token
1. Visit: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"  
3. Give it a name like "Personal Ticket Assistant"
4. Copy the token immediately (you can't see it again)
5. Add to your `.env` file as `JIRA_API_TOKEN=your_token_here`

### Testing Your Setup
```python
# Quick test script - save as test_config.py
import os
from dotenv import load_dotenv
import requests

load_dotenv()

# Test environment variables
required = ['JIRA_BASE_URL', 'JIRA_EMAIL', 'JIRA_API_TOKEN']
for var in required:
    if os.getenv(var):
        print(f"✅ {var} is set")
    else:
        print(f"❌ {var} is missing")

# Test Jira connection
try:
    url = f"{os.getenv('JIRA_BASE_URL')}/rest/api/3/myself"
    auth = (os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN'))
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        print("✅ Jira connection successful")
    else:
        print(f"❌ Jira connection failed: {response.status_code}")
except Exception as e:
    print(f"❌ Jira test error: {e}")
```

## What's Next?

This is Phase 1 - a working foundation. Future enhancements:

**Phase 2: Actions & Memory**
- File creation (scripts, documentation)
- Session memory between runs
- More sophisticated conversation handling

**Phase 3: Intelligence & Learning**  
- Learn your work patterns
- Better context awareness
- Integration with more tools (GitHub, Slack, etc.)

## Support

If you run into issues:
1. Check the troubleshooting section above
2. Test your configuration with the test script
3. Look at the console output for specific error messages
4. Start with a simple setup (OpenAI + basic Jira query) and expand from there

---

## File Structure
```
personal-ticket-assistant/
├── assistant.py          # Main application
├── .env                  # Your configuration (create this)
├── .env.example         # Template for configuration
├── requirements.txt     # Python dependencies  
├── test_config.py       # Configuration test script
└── README.md           # This file
```

Ready to become more productive with your tickets! 🚀
