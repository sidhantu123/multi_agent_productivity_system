# Gmail Agent - LangGraph Edition

A powerful, conversational Gmail assistant built with LangGraph and Pydantic AI. Manage your emails naturally through conversation, with built-in memory, smart contact caching, and comprehensive Gmail operations.

## Features

-  **AI-Powered**: OpenAI GPT-4o-mini with Pydantic AI for natural language understanding
-  **Conversation Memory**: LangGraph's built-in memory system remembers context across the conversation
-  **Full Gmail Integration**: View, search, modify, and send emails via Google Gmail API
-  **Label Management**: Organize emails with Gmail labels
-  **Smart Contact Database**: TinyDB cache for instant email address lookups
-  **Draft & Send**: Create drafts for review or send emails directly
-  **Email Address Lookup**: Finds correct email addresses by searching your email history
-  **Secure OAuth**: Google OAuth 2.0 authentication
-  **Graph Visualization**: Mermaid diagrams of conversation flow
-  **Modular Architecture**: Clean, scalable, production-ready codebase

## Quick Start

### Prerequisites

Before you begin, make sure you have:

- Python 3.11 or higher installed
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
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
OPENAI_API_KEY=sk-your-actual-key-here
```

Get your OpenAI API key from: https://platform.openai.com/api-keys

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

```bash
python main.py
```

On first run, it will:
1. Open your browser for Gmail authentication
2. Request permissions for Gmail access
3. Save the token to `config/google_token.json`
4. Start the conversation interface

## Project Structure

```
langgraph_playground/
├── main.py                    # Entry point
├── agents/                    # AI agent definitions
│   └── gmail_agent.py         # Pydantic AI Gmail agent with tools
├── graph/                     # LangGraph components
│   ├── state.py               # GmailState definitions
│   ├── nodes.py               # Node functions (user_input, gmail_agent, display)
│   ├── builder.py             # Graph construction
│   └── runner.py              # Execution logic and visualization
├── tools/                     # Agent tools
│   ├── gmail_tools.py         # Gmail API operations
│   ├── email_database.py      # TinyDB contact management
│   └── conversation_tools.py  # Conversation control
├── utils/                     # Utilities
│   └── logging.py             # Logging configuration
├── config/                    # Configuration
│   ├── settings.py            # Application constants
│   ├── google_credentials.json # OAuth client credentials (you provide)
│   └── google_token.json      # Generated auth token (gitignored)
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

## How It Works

### Architecture

```
START → user_input → gmail_agent → display_response → user_input (loop)
```

### Three-Layer Memory System

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
- `add_label_to_email()` - Apply label
- `remove_label_from_email()` - Remove label

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
- `send_email()` - Send immediately
- `reply_to_email()` - Reply to thread

### Conversation
- `end_conversation()` - Graceful exit

## Development

### Adding a New Gmail Tool

```python
# 1. Add method to GmailTools class in tools/gmail_tools.py
class GmailTools:
    def my_operation(self, param: str) -> bool:
        # Use self.service for Gmail API
        return result

# 2. Create Pydantic AI tool function
async def my_tool(ctx: RunContext[GmailDeps], param: str) -> str:
    result = ctx.deps.gmail_service.my_operation(param)
    return f"Result: {result}"

# 3. Register in agents/gmail_agent.py
gmail_agent.tool(my_tool)
```

### Adding a Database Tool

```python
# 1. Create in tools/email_database.py
async def my_db_tool(ctx: RunContext[Any], query: str) -> str:
    results = db.search(Contact.field == query)
    return format_results(results)

# 2. Register in agents/gmail_agent.py
gmail_agent.tool(my_db_tool)
```

### Adding a New Node

```python
# 1. Define in graph/nodes.py
async def my_node(state: GmailState) -> dict:
    # Your logic
    return updated_state

# 2. Register in graph/builder.py
builder.add_node("my_node", my_node)
builder.add_edge("previous_node", "my_node")
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
| **LLM** | OpenAI GPT-4o-mini | Language model |
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
2. Edit `.env` and add your OpenAI API key
3. Make sure the key starts with `sk-`

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
- [ ] Calendar integration
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
