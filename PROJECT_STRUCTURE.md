# Gmail Agent Project Structure

This document describes the modular organization of the Gmail Agent LangGraph application.

## Directory Structure

```
langgraph_playground/
├── main.py                    # Entry point - run this to start the app
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (OPENAI_API_KEY)
│
├── agents/                    # AI agent definitions
│   ├── __init__.py
│   └── gmail_agent.py         # Pydantic AI Gmail agent with tool registration
│
├── graph/                     # LangGraph components
│   ├── __init__.py            # Package exports
│   ├── state.py               # GmailState type definition
│   ├── nodes.py               # Node function implementations
│   ├── builder.py             # Graph construction logic
│   └── runner.py              # Graph execution and visualization
│
├── tools/                     # Agent tool functions
│   ├── __init__.py
│   ├── gmail_tools.py         # Gmail API operations (view, modify, send)
│   ├── email_database.py      # TinyDB contact management tools
│   └── conversation_tools.py  # Conversation control (end_conversation)
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   └── logging.py             # Logging configuration
│
├── config/                    # Configuration settings
│   ├── __init__.py
│   ├── settings.py            # Application constants
│   ├── google_credentials.json # OAuth 2.0 client credentials (user provided)
│   └── google_token.json      # Generated auth token (gitignored)
│
├── data/                      # Data storage (gitignored)
│   └── email_contacts.json    # TinyDB contact cache
│
└── logs/                      # Generated log files (gitignored)
    └── langgraph_memory_debug_*.log
```

## Module Responsibilities

### `main.py` - Application Entry Point
- Loads environment variables from `.env`
- Sets up logging configuration
- Creates the Gmail graph
- Runs the main conversation loop
- **Run this file to start the application**

### `agents/` - AI Agent Definitions

#### `gmail_agent.py`
- Creates Pydantic AI agent with OpenAI GPT-4o-mini
- Defines comprehensive system prompt with:
  - Agent identity (Sidhant Umbrajkar's assistant)
  - Email address lookup strategy
  - New sender detection workflow
  - Draft vs send logic
  - Gmail search syntax guidance
- Registers all tools with the agent
- Exports `create_gmail_agent()`, `get_gmail_agent()`, `get_gmail_tools()`

### `graph/` - LangGraph Components

#### `state.py`
- Defines `GmailState` TypedDict with fields:
  - `messages`: Conversation history (LangGraph's `add_messages` reducer)
  - `user_query`: Current user input
  - `agent_response`: Agent's response
  - `continue_conversation`: Flow control flag
  - `emails`: Cached email list from API
  - `selected_email_id`: Currently selected email
  - `email_action`: Action to perform

#### `nodes.py`
- **`user_input_node()`**: 
  - Processes user input
  - Checks conversation memory
  - Returns updated state
  
- **`gmail_agent_node()`**:
  - Authenticates Gmail service
  - Creates `GmailDeps` with email context
  - Builds conversation context from memory
  - Runs Pydantic AI agent with tools
  - Processes tool calls
  - Updates state with results
  
- **`display_response_node()`**:
  - Displays agent response to user
  - Preserves state for next turn
  
- **`should_continue()`**:
  - Routing logic based on `continue_conversation` flag
  - Returns "continue" or "end"

#### `builder.py`
- **`create_gmail_graph()`**:
  - Creates `StateGraph(GmailState)`
  - Adds nodes (user_input, gmail_agent, display_response)
  - Adds edges (START → user_input, etc.)
  - Adds conditional edges for routing
  - Compiles with:
    - `MemorySaver` for conversation memory
    - `InMemoryStore` for long-term memory
    - `interrupt_before=["user_input"]` for human-in-the-loop

#### `runner.py`
- **`run_gmail_graph()`**:
  - Main execution loop
  - Handles graph streaming
  - Processes interrupts for user input
  - Updates state via `graph.update_state()`
  
- **`visualize_graph()`**:
  - Generates Mermaid diagram
  - Displays on startup
  
- **`_display_help()`**:
  - Shows available commands
  
- **`_display_memory()`**:
  - Displays conversation history
  - Shows thread info and state keys

### `tools/` - Agent Tools

#### `gmail_tools.py`
- **`GmailDeps` dataclass**: Dependency injection container
  - `emails`: List of fetched emails
  - `gmail_service`: Authenticated Gmail API service

- **`GmailTools` class**: Gmail API wrapper
  - `authenticate()`: OAuth 2.0 flow
  - `parse_email()`: Extract email metadata
  - `list_emails()`, `search_emails()`, `get_email()`
  - `mark_as_read()`, `mark_as_unread()`
  - `archive()`, `trash()`, `delete_email()`
  - `get_labels()`, `add_label()`, `remove_label()`
  - `create_draft()`, `send_email()`, `reply_to_email()`

- **Pydantic AI Tool Functions** (async):
  - Viewing: `list_emails()`, `get_unread_emails()`, `search_emails()`, `read_email()`
  - Modification: `mark_email_as_read()`, `mark_email_as_unread()`, `archive_email()`, `trash_email()`, `delete_email()`
  - Labels: `get_labels()`, `add_label_to_email()`, `remove_label_from_email()`
  - Composition: `create_draft_email()`, `send_email()`, `reply_to_email()`
  - Lookup: `find_email_address()`

#### `email_database.py`
- TinyDB database initialization (`data/email_contacts.json`)
- **Tool Functions** (async):
  - `query_email_database()`: Fast contact lookup
  - `add_email_to_database()`: Save new contact
  - `list_all_contacts()`: View all saved contacts
  - `remove_contact_from_database()`: Delete contact
  - `check_if_human_sender()`: Detect human vs automated emails

#### `conversation_tools.py`
- `end_conversation()`: Sets `continue_conversation=False` to exit

### `utils/` - Utilities

#### `logging.py`
- Configures Python logging
- Creates timestamped log files
- Debug level for development
- Exports `setup_logging()` and `get_logger()`

### `config/` - Configuration

#### `settings.py`
- Application constants:
  - `THREAD_ID = "gmail_conversation_1"`
  - `INTERRUPT_BEFORE = ["user_input"]`
  - `SEPARATOR_LENGTH = 80`
  - `MEMORY_SEPARATOR_LENGTH = 60`
  - `GOOGLE_CREDENTIALS_PATH = "config/google_credentials.json"`
  - `GOOGLE_TOKEN_PATH = "config/google_token.json"`

#### `google_credentials.json` (User Provided)
- OAuth 2.0 client credentials from Google Cloud Console
- Format: `{"installed": {"client_id": "...", "client_secret": "...", ...}}`

#### `google_token.json` (Generated, Gitignored)
- Created after first OAuth authentication
- Contains access token and refresh token
- Auto-refreshed when expired

### `data/` - Data Storage (Gitignored)

#### `email_contacts.json` (TinyDB)
- NoSQL database for contact caching
- Structure: `{"_default": {"1": {"name": "...", "email": "...", ...}}}`
- Enables O(1) email address lookups
- Populated organically as user confirms contacts

### `logs/` - Log Files (Gitignored)

#### `langgraph_memory_debug_YYYYMMDD_HHMMSS.log`
- Timestamped debug logs
- Records state transitions, tool calls, API requests
- Useful for debugging and audit trail

## Data Flow

```
User Input (terminal)
         │
         ▼
   user_input_node
    ├─> Validate input
    ├─> Add to messages
    └─> Return state
         │
         ▼
   gmail_agent_node
    ├─> Get Gmail service
    ├─> Create GmailDeps
    ├─> Build context from memory
    ├─> Run Pydantic AI agent
    │   ├─> Agent calls tools
    │   │   ├─> Gmail API (via GmailTools)
    │   │   ├─> TinyDB (via email_database)
    │   │   └─> Returns results
    │   └─> Generate response
    ├─> Update state (emails, response)
    └─> Return state
         │
         ▼
   display_response_node
    ├─> Print response
    └─> Return to user_input (loop)
```

## Memory Architecture

### 1. LangGraph MemorySaver (Conversation History)
- Persists `messages[]` array
- Thread-based: `thread_id="gmail_conversation_1"`
- Automatic checkpointing after each node
- Accessible via `/history` command

### 2. Email State Cache (Session Context)
- `emails[]` stored in `GmailState`
- Enables "email 1", "email 2" references
- Avoids re-fetching from Gmail API
- Cleared when session ends

### 3. TinyDB Contact Database (Persistent)
- `data/email_contacts.json`
- Survives across sessions
- Fast lookups prioritized over API searches
- User-controlled additions

## Tool Workflow Patterns

### Email Address Verification Workflow
```
1. User: "Email John"
2. Agent → query_email_database("John")
3. If found: Use cached email
4. If not found:
   a. Agent → find_email_address("John") [searches all emails]
   b. If found: Ask user to add to database
   c. If not found: Ask user for email
```

### New Sender Detection Workflow
```
1. User reads email from new sender
2. Agent → check_if_human_sender(sender_email)
3. If human:
   a. Agent → query_email_database(sender_name)
   b. If not in database:
      - Ask user: "Add to database?"
      - If yes → add_email_to_database()
```

### Draft vs Send Decision Tree
```
User request
    │
    ├─> Contains "draft", "prepare", "write" → create_draft_email()
    │
    ├─> Contains "send" + confirms email → send_email()
    │
    └─> Important/complex → create_draft_email() (safety)
```

## Running the Application

```bash
# Set up environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure credentials
# 1. Add OPENAI_API_KEY to .env
# 2. Place Google OAuth credentials at config/google_credentials.json

# Run the application
python main.py
```

## First Run Flow

```
1. main.py starts
2. Loads .env (OPENAI_API_KEY)
3. Creates graph via create_gmail_graph()
4. Runs graph via run_gmail_graph()
5. Gmail authentication:
   a. Checks for config/google_token.json
   b. If missing:
      - Loads config/google_credentials.json
      - Opens browser for OAuth
      - User grants permissions
      - Saves token to google_token.json
   c. If exists: Loads and refreshes token
6. Displays Mermaid graph visualization
7. Enters conversation loop
```

## Adding New Features

### Adding a Gmail Tool
1. Add method to `GmailTools` class in `tools/gmail_tools.py`
2. Create async Pydantic AI tool function
3. Register in `agents/gmail_agent.py` via `gmail_agent.tool()`
4. Update system prompt if needed

### Adding a Database Tool
1. Create async function in `tools/email_database.py`
2. Access `db` and `Contact` for TinyDB operations
3. Register in `agents/gmail_agent.py` via `gmail_agent.tool()`
4. Update system prompt for usage guidance

### Adding a Node
1. Define async function in `graph/nodes.py`
2. Add to graph in `graph/builder.py` via `builder.add_node()`
3. Configure edges (regular or conditional)
4. Update `GmailState` if new fields needed

### Adding Configuration
1. Add constant to `config/settings.py`
2. Import where needed: `from config.settings import MY_CONSTANT`

## Gmail API Scopes

Current scopes (defined in `tools/gmail_tools.py`):
```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',    # Read, labels, archive
    'https://www.googleapis.com/auth/gmail.compose',   # Create drafts
    'https://www.googleapis.com/auth/gmail.send',      # Send emails
    'https://mail.google.com/'                         # Full access (delete)
]
```

**Note**: If you add new operations requiring different scopes:
1. Update `SCOPES` list
2. Delete `config/google_token.json`
3. Re-authenticate to get new permissions

## Error Handling

- **Gmail API Errors**: Caught and returned as user-friendly messages
- **Database Errors**: Auto-create database if missing
- **Tool Failures**: Agent receives error message, continues conversation
- **Authentication Errors**: Clear instructions to re-authenticate

## Testing Checklist

- [ ] First-time OAuth flow works
- [ ] Token refresh works on subsequent runs
- [ ] Email listing shows correct data
- [ ] Email search uses correct query syntax
- [ ] Email modification operations succeed
- [ ] Draft creation works
- [ ] Email sending works with verified addresses
- [ ] Database queries return expected results
- [ ] Database additions persist across sessions
- [ ] New sender detection triggers appropriately
- [ ] Conversation memory persists across turns
- [ ] `/history` command shows correct data
- [ ] `quit` exits gracefully
- [ ] Logs are created with correct format

## Benefits of This Structure

- **Modularity**: Each file has a single, clear purpose
- **Testability**: Components can be tested in isolation
- **Scalability**: Easy to add new tools, nodes, or capabilities
- **Maintainability**: Clear separation of concerns
- **Reusability**: Tools and utilities work independently
- **Security**: Credentials and tokens properly isolated
- **Debuggability**: Comprehensive logging at all levels
- **Documentation**: Self-documenting code with clear structure

## Common Files to Edit

| Task | Files to Modify |
|------|----------------|
| Add Gmail operation | `tools/gmail_tools.py`, `agents/gmail_agent.py` |
| Add database query | `tools/email_database.py`, `agents/gmail_agent.py` |
| Change conversation flow | `graph/builder.py`, `graph/nodes.py` |
| Update agent behavior | `agents/gmail_agent.py` (system prompt) |
| Add configuration | `config/settings.py` |
| Modify state structure | `graph/state.py` |
| Change authentication | `tools/gmail_tools.py` (SCOPES, authenticate method) |

## Environment Variables

Required in `.env`:
```bash
OPENAI_API_KEY=sk-...  # Your OpenAI API key
```

Optional:
```bash
LOG_LEVEL=DEBUG        # Logging level (default: DEBUG)
```

## Gitignore Strategy

Protected files (gitignored):
- `config/google_token.json` - OAuth token (regenerated)
- `data/` - Contact database (user-specific)
- `logs/` - Debug logs (temporary)
- `.env` - API keys (secrets)
- `__pycache__/` - Python cache

Committed files:
- `config/google_credentials.json` - OAuth client ID (can be shared in private repo, or gitignored for public repos)
- `.env.example` - Template for environment variables
- All Python source code
- Documentation files

## Quick Command Reference

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python main.py

# View logs
tail -f logs/langgraph_memory_debug_*.log

# Reset authentication
rm config/google_token.json

# Clear contact database
rm data/email_contacts.json

# Check graph visualization
# (Run app, copy Mermaid output, paste to https://mermaid.live)
```

## Extending to Multi-Agent System

To add more agents (e.g., Calendar, Tasks):

1. **Create new agent**: `agents/calendar_agent.py`
2. **Create new tools**: `tools/calendar_tools.py`
3. **Update state**: Add calendar fields to `GmailState` (or create `UnifiedState`)
4. **Add routing**: Create router node in `graph/nodes.py` to decide which agent to use
5. **Update graph**: Add conditional edges based on user intent

Example routing:
```python
def route_to_agent(state: UnifiedState) -> str:
    query = state["user_query"].lower()
    if "email" in query or "gmail" in query:
        return "gmail_agent"
    elif "calendar" in query or "meeting" in query:
        return "calendar_agent"
    else:
        return "default_agent"
```
