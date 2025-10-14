# Multi-Agent Productivity System (Gmail + Calendar)

A modular, conversational productivity system built with LangGraph and Pydantic AI. It currently includes two agents: a Gmail agent and a Google Calendar agent. Manage emails and calendar events naturally through conversation, with built-in memory, smart contact caching, and comprehensive Google integrations. An orchestrator agent will soon route intents across Gmail and Calendar for a unified experience.

---

## Calendar Agent (Standalone)

In addition to the Gmail agent, this repository now includes a Google Calendar agent built with Pydantic AI. The Calendar agent currently runs as a standalone CLI service for development and testing.

Planned next step: integrate the Calendar agent into the existing LangGraph architecture with an orchestrator agent that can route user requests to Gmail and/or Calendar based on intent.

## System Features

- **AI-Powered**: OpenAI (e.g., gpt-4o-mini) with Pydantic AI for natural language understanding
- **Conversation Memory**: LangGraph's built-in memory system remembers context across the conversation
- **Full Gmail Integration**: View, search, modify, and send emails via Google Gmail API
- **Smart Unsubscribe**: Automatic one-click unsubscribe or guided manual unsubscribe from marketing emails
- **Label Management**: Create, delete, and organize emails with Gmail labels
- **Smart Contact Database**: TinyDB cache for instant email address lookups
- **Draft & Send**: Create drafts for review or send emails directly (including draft replies)
- **Email Address Lookup**: Finds correct email addresses by searching your email history
- **Secure OAuth**: Google OAuth 2.0 authentication
- **Graph Visualization**: Separate utility to generate Mermaid diagrams of conversation flow
- **Modular Architecture**: Clean, organized, production-ready codebase with one tool per file

## Calendar Agent Features
- **Event Management**: List, get details, create, update, and delete events
- **Time Awareness**: Tool to retrieve current date/time on demand
- **Attendees**: Add/remove attendees from events
- **RSVP**: Update RSVP status (going, not going, tentative)
- **Google Meet**: Create events with Meet or add Meet link to existing events
- **Notifications**: Configure reminders (e.g., 10 and 30 minutes before)
- **Contact Database**: Reuse TinyDB tools to add/list/query/remove contacts
- **PST Context**: Assumes user timezone is PST for natural language times

## Quick Start

### Prerequisites

Before you begin, make sure you have:

- Python 3.11 or higher installed
- OpenAI API key ([create here](https://platform.openai.com/api-keys))
- Google Cloud Project ([create here](https://console.cloud.google.com/))
- Gmail API enabled in your Google Cloud Project
- OAuth 2.0 Desktop credentials downloaded

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd langgraph_playground

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

**Edit `.env` file:**
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

Get your OpenAI API key from: https://platform.openai.com/api-keys

### Google Calendar Setup (Standalone Agent)

1. Enable the Google Calendar API in your Google Cloud project
2. Use the same OAuth Desktop credentials JSON used for Gmail (or create a new one)
3. Save credentials as `config/google_credentials.json`
4. On first run, a Calendar token will be created at `config/google_calendar_token.json`

Run the standalone Calendar agent CLI:

```bash
python test_calendar.py
```

Examples you can try:
- "what events do I have tomorrow"
- "schedule a meeting tomorrow at 2pm with a Google Meet"
- "add mangesh to the team standup as an attendee"
- "mark me as going for the 3pm meeting"
- "set 10 and 30 minute reminders for that event"

### LangSmith Setup (Optional - Recommended for Production)

LangSmith provides observability, debugging, and monitoring for your Gmail agent. It automatically traces:
- Every conversation turn
- All tool calls (email operations)
- LLM requests and responses
- Errors and latency

**To enable LangSmith:**

1. Sign up at https://smith.langchain.com
2. Get your API key from the settings
3. Add to your `.env` file:
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=Gmail-Agent
```

That's it! LangGraph will automatically send traces to LangSmith. View them at https://smith.langchain.com

**Benefits:**
- Visual timeline of every conversation
- Debug tool call failures
- Monitor agent performance
- Track token usage and costs
- A/B test system prompts
- Human feedback collection

### Gmail API Setup

1. **Create Google Cloud Project**: 
   - Go to https://console.cloud.google.com/
   - Create a new project or select an existing one

2. **Enable Gmail API**:
   - Navigate to "APIs & Services" → "Enable APIs and Services"
   - Search for "Gmail API"
   - Click "Enable"

3. **Configure OAuth Consent Screen**:
   - Go to "APIs & Services" → "OAuth consent screen"
   - Select "External" user type (unless you have Google Workspace)
   - Fill in required fields:
     - App name: "Gmail Agent" (or your choice)
     - User support email: Your email
     - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Skip this for now (click "Save and Continue")
   - **Add Test Users**: Add your Gmail address under "Test users"
   - Click "Save and Continue"

4. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Gmail Agent Client" (or your choice)
   - Click "Create"
   - Click "Download JSON" (download icon)

5. **Save Credentials**:
   - Rename the downloaded file to `google_credentials.json`
   - Move it to the `config/` directory in your project:
     ```bash
     mv ~/Downloads/client_secret_*.json config/google_credentials.json
```

### Running the Application

**Start the agent:**
```bash
python main.py
```

**View graph structure (optional):**
```bash
python graph_visualization.py
```

On first run, it will:
1. Open your browser for Gmail authentication
2. Request permissions for Gmail access
3. Save the token to `config/google_token.json`
4. Start the conversation interface

To run the Calendar agent (standalone CLI):

```bash
python test_calendar.py
```

## Project Structure

```
langgraph_playground/
├── main.py                          # Entry point
├── graph_visualization.py           # Standalone graph visualization utility
├── agents/                          # AI agent definitions
│   ├── gmail_agent.py               # Pydantic AI Gmail agent with tools
│   └── calendar_agent.py            # Pydantic AI Calendar agent (standalone for now)
├── graph/                           # LangGraph components
│   ├── state.py                     # GmailState definitions
│   ├── nodes.py                     # Node functions (user_input, gmail_agent)
│   ├── builder.py                   # Graph construction
│   └── runner.py                    # Execution logic
├── tools/                           # Agent tools (modular structure)
│   ├── gmail_tools/                 # Gmail operations (21 files)
│   │   ├── __init__.py              # Exports all Gmail tools
│   │   ├── core.py                  # GmailTools service class & GmailDeps
│   │   ├── list_emails.py           # List recent emails
│   │   ├── search_emails.py         # Search with Gmail query syntax
│   │   ├── read_email.py            # Read full email content
│   │   ├── mark_read.py             # Mark as read
│   │   ├── mark_unread.py           # Mark as unread
│   │   ├── archive_email.py         # Archive email
│   │   ├── trash_email.py           # Move to trash
│   │   ├── delete_email.py          # Permanently delete
│   │   ├── get_labels.py            # List all labels
│   │   ├── create_label.py          # Create new label
│   │   ├── delete_label.py          # Delete label
│   │   ├── add_label.py             # Add label to email
│   │   ├── remove_label.py          # Remove label from email
│   │   ├── send_email.py            # Send new email
│   │   ├── reply_to_email.py        # Reply to email
│   │   ├── create_draft.py          # Create draft email
│   │   ├── create_draft_reply.py    # Create draft reply
│   │   ├── find_email_address.py    # Search for email addresses
│   │   ├── unsubscribe.py           # Smart unsubscribe tool
│   │   └── get_unread.py            # Get unread emails
│   ├── database_tools/              # Contact database (7 files)
│   │   ├── __init__.py              # Exports all database tools
│   │   ├── db.py                    # TinyDB utilities
│   │   ├── query_database.py        # Query contacts
│   │   ├── add_contact.py           # Add contact
│   │   ├── check_human_sender.py    # Detect human vs automated
│   │   ├── list_contacts.py         # List all contacts
│   │   └── remove_contact.py        # Remove contact
│   ├── conversation_tools/          # Conversation control (2 files)
│   └── calendar_tools/              # Google Calendar operations (multiple files)
│       ├── __init__.py              # Exports all Calendar tools
│       ├── core.py                  # CalendarTools service class & CalendarDeps
│       ├── list_events.py           # List upcoming events
│       ├── get_event.py             # Get event details
│       ├── create_event.py          # Create new event
│       ├── update_event.py          # Modify time/details
│       ├── manage_attendees.py      # Add/remove attendees
│       ├── delete_event.py          # Delete event
│       ├── update_rsvp.py           # RSVP updates
│       ├── get_current_time.py      # Current date/time tool
│       ├── add_google_meet.py       # Add Meet / create event with Meet
│       └── set_reminders.py         # Configure event reminders
│       ├── __init__.py              # Exports conversation tools
│       └── end_conversation.py      # End conversation tool
├── utils/                     # Utilities
│   └── logging.py             # Logging configuration
├── config/                    # Configuration
│   ├── settings.py            # Application constants
│   ├── google_credentials.json # OAuth client credentials (you provide)
│   ├── google_token.json      # Gmail auth token (gitignored)
│   └── google_calendar_token.json # Calendar auth token (gitignored)
├── data/                      # Data storage
│   └── email_contacts.json    # TinyDB contact cache (gitignored)
└── logs/                      # Generated logs (gitignored)
```

## Usage

### Basic Conversations

```
You: Show me my recent emails
Agent: [Lists last 10 emails with numbers]

You: Read email 3
Agent: [Shows full content of email #3]

You: Mark it as read
Agent: Email marked as read

You: Show unread emails
Agent: [Lists unread emails only]
```

### Searching Emails

```
You: Find emails from john@example.com
Agent: [Shows emails from John]

You: Search for emails about "meeting" after January 1st
Agent: [Uses Gmail query: subject:meeting after:2024/01/01]
```

### Email Organization

```
You: Archive email 1
Agent: Email archived

You: Add label "Important" to email 2
Agent: Label added

You: What labels are available?
Agent: [Lists all Gmail labels]

You: Delete email 5
Agent: WARNING: This will permanently delete the email...
```

### Sending Emails

```
You: Draft an email to Mangesh about the meeting
Agent: Let me check the database...
      Found: mangesh@company.com
      [Creates draft]
      Draft created! You can review in Gmail

You: Send a quick thank you to Sarah
Agent: Let me check the database...
      Found: sarah@example.com
      Email sent successfully!
```

### Unsubscribing from Emails

```
You: Unsubscribe from email 3
Agent: Found unsubscribe options for:
      From: newsletter@company.com
      
      Method 1: One-Click Unsubscribe (Automatic)
      Status: Successfully unsubscribed!
      
You: Unsubscribe from email 5
Agent: Found unsubscribe options for:
      From: marketing@service.com
      
      Method 1: Web Link
      URL: https://service.com/unsubscribe?id=123
      Action Required: Click the link above to unsubscribe
```

### Contact Management

```
You: Do we have an email for John?
Agent: Let me check the database...
      Found: john@example.com

You: Add alice@example.com to the database as Alice Smith
Agent: Added Alice Smith to contacts database

You: Show all contacts
Agent: [Lists all saved contacts with emails]
```

### Commands

- `/help` - Show available commands
- `/history` or `/memory` - View conversation history
- `/context` - Same as /history
- `quit` or `exit` - End conversation

### Calendar Agent (Standalone) Usage

Run:
```bash
python test_calendar.py
```

What you can say:
- "show my upcoming meetings"
- "schedule a meeting tomorrow at 2pm with a Google Meet"
- "add sarah@example.com to the standup"
- "mark me as maybe for the client sync"
- "set 10 and 30 minute reminders"

## How It Works

### Architecture

```
START → user_input ⇄ gmail_agent (bidirectional loop)
                ↓
               END

Planned Orchestration (Upcoming):

```
START → user_input ⇄ orchestrator_agent → [gmail_agent, calendar_agent]
                                       ↘ possibly both in sequence
                 ↓
                END
```

The orchestrator will route intents to Gmail and/or Calendar agents within the LangGraph, enabling a single unified assistant.
```

**Bidirectional Flow:**
- User input triggers agent
- Agent processes and responds
- Loop continues until user exits

### Three-Layer Memory System (Gmail)

1. **LangGraph MemorySaver**: Conversation history across turns
2. **Email State Cache**: Fetched emails referenced by number
3. **TinyDB Contact Database**: Persistent contact lookups

### Email Address Lookup Strategy

**Priority Order:**
1. **First**: Check TinyDB database (instant O(1) lookup)
2. **Fallback**: Search all emails using `find_email_address()` (slower)
3. **Learn**: Ask user to add found addresses to database

**Example:**
```
User: "Email Mangesh"
Agent: 
  1. Checks database → Found! Use cached email
  
User: "Email NewPerson"
Agent:
  1. Checks database → Not found
  2. Searches emails → Found newperson@example.com
  3. Asks: "Add to database for faster lookups?"
```

### New Contact Detection

When you view an email from a new sender:
1. Agent checks if sender is human (vs automated newsletter)
2. If human AND not in database, asks to save
3. Builds contact database organically over time

### Draft vs Send Logic

**Creates Draft:**
- User says "draft", "prepare", "write but don't send"
- Important or complex emails
- Agent wants you to review first

**Sends Directly:**
- User explicitly says "send"
- Quick, simple messages
- After confirming email address with user

## Gmail Agent Tools

### Viewing
- `list_emails()` - List recent emails
- `get_unread_emails()` - Filter unread only
- `search_emails()` - Gmail query syntax
- `read_email()` - Full email content

### Modification
- `mark_email_as_read()` / `mark_email_as_unread()`
- `archive_email()` - Move to archive
- `trash_email()` - Move to trash
- `delete_email()` - Permanent deletion

### Labels
- `get_labels()` - List all labels
- `create_label()` - Create new label
- `delete_label()` - Delete label
- `add_label_to_email()` - Apply label
- `remove_label_from_email()` - Remove label

### Unsubscribe
- `unsubscribe_from_email()` - Smart unsubscribe (automatic + manual)

### Contact Database (TinyDB)
- `query_email_database()` - Fast lookup
- `add_email_to_database()` - Save contact
- `list_all_contacts()` - View all
- `remove_contact_from_database()` - Delete contact
- `check_if_human_sender()` - Detect human vs bot

### Email Lookup (Fallback)
- `find_email_address()` - Search email history

### Composition
- `create_draft_email()` - Create draft
- `create_draft_reply()` - Create draft reply
- `send_email()` - Send immediately
- `reply_to_email()` - Reply to thread

### Conversation
- `end_conversation()` - Graceful exit

## Calendar Agent Tools (Standalone)

### Viewing
- `list_upcoming_events()` - List upcoming events
- `get_event_details()` - Get event details by ID

### Creation
- `schedule_meeting()` - Create a new event
- `schedule_meeting_with_google_meet()` - Create new event with Meet

### Modification
- `modify_meeting_time()` - Reschedule
- `update_meeting_details()` - Update title/description/location
- `add_attendees_to_meeting()` / `remove_attendees_from_meeting()`
- `update_rsvp_status()` - accepted/declined/tentative/needsAction
- `add_google_meet_to_event()` - Add Meet to an existing event
- `configure_event_notifications()` - Set reminders (e.g., [10, 30])

### Utility
- `get_current_datetime()` - Always use to resolve "today/now" and relative dates

## Development

### Adding a New Gmail Tool

**With modular structure, tools are now organized in separate files:**

```python
# 1. Add method to GmailTools class in tools/gmail_tools/core.py
class GmailTools:
    def my_operation(self, param: str) -> bool:
        # Use self.service for Gmail API
        return result

# 2. Create new file: tools/gmail_tools/my_tool.py
from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps

async def my_tool(ctx: RunContext[GmailDeps], param: str) -> str:
    result = ctx.deps.gmail_service.my_operation(param)
    return f"Result: {result}"

# 3. Export in tools/gmail_tools/__init__.py
from tools.gmail_tools.my_tool import my_tool

__all__ = [
    # ... existing exports ...
    'my_tool',
]

# 4. Register in agents/gmail_agent.py
from tools.gmail_tools import my_tool
# ... in create_gmail_agent():
gmail_agent.tool(my_tool)
```

### Adding a Database Tool

```python
# 1. Create new file: tools/database_tools/my_tool.py
from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps
from tools.database_tools.db import get_db
from tinydb import Query

async def my_db_tool(ctx: RunContext[GmailDeps], query: str) -> str:
    db = get_db()
    results = db.search(Query().field == query)
    db.close()
    return f"Found {len(results)} results"

# 2. Export in tools/database_tools/__init__.py
from tools.database_tools.my_tool import my_db_tool

# 3. Register in agents/gmail_agent.py
from tools.database_tools import my_db_tool
gmail_agent.tool(my_db_tool)
```

### Running Tests

```bash
# Test graph compilation
python -c "from graph.builder import create_gmail_graph; graph = create_gmail_graph(); print('✓ Graph OK')"

# Test tool imports
python -c "from tools.gmail_tools import unsubscribe_from_email; print('✓ Tools OK')"

# View graph visualization
python graph_visualization.py
```

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed system design, workflows, and patterns
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Module organization guide

## Gmail Search Syntax

The agent supports Gmail's powerful search syntax:

```
from:john@example.com          # Emails from John
to:sarah@example.com           # Emails to Sarah
subject:meeting                # Subject contains "meeting"
has:attachment                 # Has attachments
is:unread                      # Unread emails
is:starred                     # Starred emails
after:2024/01/01               # After date
before:2024/12/31              # Before date
newer_than:7d                  # Last 7 days
older_than:30d                 # Older than 30 days
in:inbox                       # In inbox
in:spam                        # In spam
label:important                # Has "Important" label
```

Combine operators:
```
from:john subject:meeting after:2024/01/01
```

## Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Orchestration** | LangGraph | State management, conversation flow |
| **AI Agent** | Pydantic AI | Tool calling, NLU |
| **LLM** | OpenAI (e.g., gpt-4o-mini) | Language model |
| **Email API** | Google Gmail API | Email operations |
| **Database** | TinyDB | Contact cache (NoSQL) |
| **Auth** | Google OAuth 2.0 | Secure Gmail access |
| **Logging** | Python logging | Debug & audit |

## Troubleshooting

### "Error 403: access_denied"
**Problem**: App hasn't completed Google verification  
**Solution**: 
1. Go to Google Cloud Console → OAuth consent screen
2. Add your Gmail address under "Test users"
3. Re-run the app and authenticate

### "Insufficient authentication scopes"
**Problem**: Token created with old/limited scopes  
**Solution**:
```bash
rm config/google_token.json
python main.py  # Re-authenticate with new scopes
```

### "No module named 'pydantic_ai'"
**Problem**: Dependencies not installed  
**Solution**:
```bash
pip install -r requirements.txt
```

### Agent doesn't find email address
**Problem**: Not in database and not found in emails  
**Solution**:
1. Manually search your Gmail for the person
2. When found, ask agent: "Add [name] <[email]> to database"

### "No such file or directory: 'config/google_credentials.json'"
**Problem**: OAuth credentials file not found  
**Solution**:
1. Download credentials from Google Cloud Console (see Gmail API Setup above)
2. Save the file as `config/google_credentials.json`
3. Make sure you're in the project root directory

### "OPENAI_API_KEY not found"
**Problem**: Environment variable not set  
**Solution**:
1. Create `.env` file from `.env.example`: `cp .env.example .env`
2. Edit `.env` and add your OpenAI API key from https://platform.openai.com/api-keys
3. Key should start with `AIza`

## Security & Privacy

- **OAuth 2.0**: No password storage, token-based auth
- **Local Storage**: All data stored locally, never transmitted to third parties
- **Minimal Scopes**: Only requests necessary Gmail permissions
- **Gitignored Secrets**: Credentials and tokens never committed
- **User Control**: All destructive actions require confirmation

## Example Session

```
=================================================================
Gmail Agent - LangGraph Edition with Built-in Memory
=================================================================

You: Show me unread emails

Processing: Show me unread emails

Tool Calls:
   - get_unread_emails()

Answer: Here are your 3 unread emails:
1. From: john@example.com - "Meeting Tomorrow"
2. From: sarah@company.com - "Q4 Report"  
3. From: newsletter@site.com - "Weekly Updates"

You: Mark email 1 as read and archive it

Processing: Mark email 1 as read and archive it

Tool Calls:
   - mark_email_as_read()
   - archive_email()

Answer: Email marked as read
Email archived successfully

You: I see an email from newsletter@site.com - is that a human?

Processing: I see an email from newsletter@site.com - is that a human?

Tool Calls:
   - check_if_human_sender()

Answer: No, newsletter@site.com appears to be an automated newsletter, 
not a human sender. I won't suggest adding it to your contacts database.

You: Draft an email to john about the meeting

Processing: Draft an email to john about the meeting

Tool Calls:
   - query_email_database()
   - create_draft_email()

Answer: Let me check the database...
Found: john@example.com

Draft created successfully!
To: john@example.com
Subject: Re: Meeting Tomorrow

You can review and send this draft from Gmail.

You: quit

Goodbye!
```

## Future Enhancements

- [ ] Attachment upload/download support
- [ ] Email templates with variables
- [ ] Orchestrator agent to route Gmail/Calendar within LangGraph
- [ ] Integrate Calendar agent into LangGraph graph and state
- [ ] Email analytics and insights
- [ ] Multi-account support
- [ ] Smart reply suggestions
- [ ] Natural language date parsing
- [ ] Batch operations (bulk actions)
- [ ] Email categorization/auto-labeling

## License

MIT

## Author

Sidhant Umbrajkar

---

**Built with LangGraph for orchestration, Pydantic AI for intelligence, and Gmail API for email operations.**
