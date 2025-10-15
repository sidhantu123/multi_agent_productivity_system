# Gmail Agent Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                     (Entry Point)                            │
│  • Loads environment                                         │
│  • Sets up logging                                           │
│  • Creates graph                                             │
│  • Runs application                                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────┐      ┌──────────────┐
│ utils/       │      │ config/      │
│ logging.py   │      │ settings.py  │
└──────────────┘      └──────────────┘
        │                     │
        └──────────┬──────────┘
                   │
                   ▼
        ┌──────────────────┐
        │   graph/         │
        │   builder.py     │
        │  (Creates Graph) │
        └────────┬─────────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
     ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ state.py│ │ nodes.py│ │runner.py│
│         │ │         │ │         │
│GmailSta │ │ Node    │ │ Exec    │
│te       │ │ Funcs   │ │ Loop    │
└─────────┘ └────┬────┘ └─────────┘
                 │
                 ▼
          ┌─────────────┐
          │  agent.py   │
          │ (Pydantic)  │
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │   tools/    │
          │ • gmail     │
          │ • email_db  │
          │ • convers.  │
          └─────────────┘
                 │
                 ▼
          ┌─────────────┐
          │  data/      │
          │  TinyDB     │
          │ (contacts)  │
          └─────────────┘
```

## Component Flow

### 1. **Startup Flow**
```
main.py
  ├─> load_dotenv()
  ├─> setup_logging()
  ├─> create_graph()
  │     ├─> Create StateGraph(UnifiedState)
  │     ├─> Add nodes (from nodes.py)
  │     ├─> Add edges
  │     └─> Compile with memory
  └─> run_gmail_graph()
        └─> Event loop
```

### 2. **Request Flow**
```
User Input
  ↓
user_input_node (graph/nodes.py)
  ├─> Validate input
  ├─> Check memory
  └─> Return state
  ↓
gmail_agent_node (graph/nodes.py)
  ├─> Build conversation context
  ├─> Get Gmail service (authenticate if needed)
  ├─> Create GmailDeps (email context + service)
  ├─> Call get_gmail_agent() (agent.py)
  │     ├─> Create agent (lazy init)
  │     ├─> Register tools (tools/)
  │     └─> Run with context
  ├─> Process tool calls
  ├─> Update state with emails
  └─> Return response
  ↓
display_response_node (graph/nodes.py)
  ├─> Display response
  └─> Return to user_input
```

### 3. **Memory Flow**
```
LangGraph MemorySaver
  ├─> Checkpointer stores state
  ├─> Thread ID: gmail_conversation_1
  └─> Messages persisted automatically

Email Context Memory
  ├─> emails[] stored in state
  ├─> selected_email_id tracked
  └─> Referenced by number in conversation

TinyDB Contact Cache
  ├─> data/email_contacts.json
  ├─> Fast lookups for known contacts
  └─> Populated as user confirms contacts
```

### 4. **Gmail API Authentication Flow**
```
First Run:
  ├─> Check for config/google_token.json
  ├─> If missing:
  │     ├─> Load config/google_credentials.json
  │     ├─> Launch OAuth flow (browser)
  │     ├─> User grants permissions
  │     └─> Save token to google_token.json
  └─> Build Gmail service with authenticated credentials

Subsequent Runs:
  ├─> Load existing google_token.json
  ├─> Refresh if expired
  └─> Build Gmail service
```

## Module Dependencies

```
main.py
  ├── utils.logging
  ├── graph.builder
  └── graph.runner
        ├── graph.state
        ├── graph.nodes
        │     ├── agents.gmail_agent (lazy)
        │     └── tools.gmail_tools
        │           ├── Google Gmail API
        │           └── tools.email_database
        │                 └── TinyDB
        └── config.settings
```

## Data Flow

```
┌──────────┐
│   User   │
└────┬─────┘
     │ input
     ▼
┌──────────────┐
│ UnifiedState │ ◄──┐
│ (graph/state)│    │
│ • messages   │    │
│ • emails[]   │    │
│ • query      │    │
└──────┬───────┘    │
       │            │
       ▼            │
  ┌─────────┐      │
  │  Nodes  │      │ LangGraph
  │ (logic) │      │ Memory
  └────┬────┘      │
       │            │
       ▼            │
  ┌─────────┐      │
  │  Agent  │      │
  │ (AI+tools)     │
  └────┬────┘      │
       │            │
       ▼            │
  ┌─────────┐      │
  │ Gmail API│     │
  │ + TinyDB │     │
  └────┬────┘      │
       │            │
       ▼            │
┌──────────────┐   │
│   Response   │───┘
└──────────────┘
```

## Design Patterns Used

1. **Separation of Concerns**: Each module has one responsibility
2. **Dependency Injection**: GmailDeps injected into tools via RunContext
3. **Lazy Initialization**: Agent and Gmail service created only when needed
4. **Factory Pattern**: `create_graph()`, `create_gmail_agent()`
5. **State Machine**: LangGraph StateGraph pattern
6. **Observer Pattern**: Event streaming in runner
7. **Cache-Aside Pattern**: TinyDB database for contact lookups

## Gmail Agent Workflow

### Email Address Lookup Strategy

```
User: "Send email to Mangesh"
         │
         ▼
┌────────────────────┐
│ 1. Query Database  │ (FAST - O(1) lookup)
│   TinyDB search    │
└────────┬───────────┘
         │
    ┌────┴────┐
    │ Found?  │
    └────┬────┘
         │
    ┌────┴────────────────────────┐
    │                             │
   YES                           NO
    │                             │
    ▼                             ▼
Use cached          ┌──────────────────────┐
email address       │ 2. Search Emails     │ (SLOW - searches all emails)
                    │   find_email_address │
                    └──────────┬───────────┘
                               │
                          ┌────┴────┐
                          │ Found?  │
                          └────┬────┘
                               │
                          ┌────┴────┐
                          │   YES   │
                          └────┬────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Ask to Add to DB     │
                    └──────────────────────┘
```

### New Human Sender Detection

```
User views/reads email
         │
         ▼
┌────────────────────┐
│ Check sender with  │
│check_if_human_sender│
└────────┬───────────┘
         │
    ┌────┴────┐
    │ Human?  │
    └────┬────┘
         │
    ┌────┴─────┐
    │   YES    │
    └────┬─────┘
         │
         ▼
┌────────────────────┐
│  In database?      │
└────────┬───────────┘
         │
    ┌────┴────┐
    │   NO    │
    └────┬────┘
         │
         ▼
┌────────────────────┐
│ Ask user to add    │
│ to database        │
└────────────────────┘
```

## Extension Points

### Adding a New Node
```python
# 1. Define in graph/nodes.py
async def my_new_node(state: UnifiedState) -> dict:
    # logic here
    return updated_state

# 2. Register in graph/builder.py
builder.add_node("my_node", my_new_node)
builder.add_edge("previous_node", "my_node")
```

### Adding a New Gmail Tool
```python
# 1. Create class method in tools/gmail_tools.py (GmailTools class)
def my_gmail_operation(self, param: str) -> bool:
    """Docstring"""
    # Use self.service for Gmail API calls
    return result

# 2. Create Pydantic AI tool function in tools/gmail_tools.py
async def my_tool(ctx: RunContext[GmailDeps], param: str) -> str:
    """Docstring for AI to understand when to use this"""
    result = ctx.deps.gmail_service.my_gmail_operation(param)
    return f"Result: {result}"

# 3. Register in agents/gmail_agent.py
gmail_agent.tool(my_tool)
```

### Adding a New Database Tool
```python
# 1. Create in tools/email_database.py
async def my_db_tool(ctx: RunContext[Any], param: str) -> str:
    """Tool that uses TinyDB"""
    # Access db and Contact query
    results = db.search(Contact.field == param)
    return formatted_results

# 2. Register in agents/gmail_agent.py
gmail_agent.tool(my_db_tool)
```

### Adding Configuration
```python
# 1. Add to config/settings.py
MY_SETTING = "value"

# 2. Import where needed
from config.settings import MY_SETTING
```

## Security Considerations

### Gmail API Authentication
- **OAuth 2.0**: User consent required for all operations
- **Scopes**: Minimal scopes requested (modify, compose, send, full access for deletion)
- **Token Storage**: `config/google_token.json` (gitignored)
- **Credentials**: `config/google_credentials.json` (OAuth client ID/secret)

### Data Storage
- **Contact Database**: `data/email_contacts.json` (gitignored)
- **No Email Content Stored**: Only metadata and addresses cached
- **Local Only**: All data stored locally, not transmitted externally

### Google Cloud Console Setup
- App must be in "Testing" mode or published
- Test users must be explicitly added in OAuth consent screen
- Scopes must match requested permissions

## Error Handling Strategy

1. **Gmail API Errors**:
   - HttpError 403: Insufficient permissions → Re-authenticate
   - HttpError 404: Email not found → User-friendly message
   - HttpError 400: Invalid request → Validate inputs

2. **Database Errors**:
   - File not found → Auto-create database
   - Invalid query → Graceful fallback

3. **Agent Errors**:
   - Tool call failures → Return error message to user
   - Continue conversation despite errors

## Performance Optimizations

1. **Contact Database Cache**:
   - O(1) lookups for known contacts
   - Avoids expensive Gmail API searches
   - User-controlled additions

2. **Email Context Preservation**:
   - Emails stored in state after fetching
   - Reference by number without re-fetching
   - Reduces API calls

3. **Lazy Initialization**:
   - Agent created on first use
   - Gmail service authenticated once per session

## Benefits of This Architecture

- **Testable**: Mock any component
- **Maintainable**: Clear file boundaries
- **Scalable**: Easy to extend with new tools
- **Debuggable**: Isolated concerns
- **Reusable**: Components work independently
- **Secure**: OAuth-based authentication
- **Efficient**: Multi-level caching strategy
- **Professional**: Industry best practices

## State Structure

```python
class UnifiedState(TypedDict):
    messages: Annotated[List[dict], add_messages]  # Conversation history
    user_query: str                                 # Current user input
    agent_response: str                             # Agent's response
    continue_conversation: bool                     # Flow control
    emails: Optional[List[dict]]                    # Fetched emails cache
    selected_email_id: Optional[str]                # Currently selected email
    email_action: Optional[str]                     # Action to perform
```

## Tool Categories

### 1. **Viewing Tools**
- `list_emails()` - List recent emails
- `get_unread_emails()` - Filter unread only
- `search_emails()` - Gmail query syntax search
- `read_email()` - Get full email content

### 2. **Modification Tools**
- `mark_email_as_read()` / `mark_email_as_unread()`
- `archive_email()` - Move to archive
- `trash_email()` - Move to trash
- `delete_email()` - Permanent deletion (requires full scope)

### 3. **Label Management Tools**
- `get_labels()` - List all Gmail labels
- `add_label_to_email()` - Apply label
- `remove_label_from_email()` - Remove label

### 4. **Contact Database Tools** (TinyDB)
- `query_email_database()` - Fast contact lookup
- `add_email_to_database()` - Save new contact
- `list_all_contacts()` - View all saved contacts
- `remove_contact_from_database()` - Delete contact
- `check_if_human_sender()` - Detect human vs automated emails

### 5. **Email Lookup Tools** (Fallback)
- `find_email_address()` - Search email history for addresses

### 6. **Composition Tools**
- `create_draft_email()` - Create draft (review before sending)
- `send_email()` - Send email immediately
- `reply_to_email()` - Reply to existing thread

### 7. **Conversation Control**
- `end_conversation()` - Graceful exit

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | LangGraph | Conversation flow, state management, memory |
| **AI Agent** | Pydantic AI | Tool calling, natural language understanding |
| **LLM** | OpenAI GPT-4o-mini | Language model for agent intelligence |
| **Email API** | Google Gmail API | Email operations (read, write, modify) |
| **Database** | TinyDB | NoSQL contact cache |
| **Auth** | Google OAuth 2.0 | Secure Gmail access |
| **Logging** | Python logging | Debug and audit trail |

## Conversation Memory Architecture

### Three-Layer Memory System

1. **LangGraph MemorySaver** (Conversation History)
   - Persists `messages[]` across turns
   - Thread-based isolation
   - Automatic checkpointing

2. **State Email Cache** (Session Context)
   - Stores fetched `emails[]` in state
   - Enables "email 1", "email 2" references
   - Cleared on session end

3. **TinyDB Contact Database** (Persistent Knowledge)
   - Survives across sessions
   - User-controlled additions
   - Fast O(1) lookups

## Human-in-the-Loop Patterns

### Interrupt-Before Pattern
```python
# In config/settings.py
INTERRUPT_BEFORE = ["user_input"]

# Agent waits at user_input node for input
# Enables conversational turn-taking
```

### Confirmation Workflows

1. **Email Sending**:
   - Agent finds/confirms email address
   - Shows details before sending
   - Waits for user confirmation

2. **Database Additions**:
   - Agent detects new human sender
   - Asks user if they want to save
   - Only adds on explicit consent

3. **Destructive Operations**:
   - Delete warns "Cannot be undone"
   - Clear action description
   - User can cancel

## Extending the System

### Add a Calendar Agent
```python
# 1. Create agents/calendar_agent.py
# 2. Create tools/calendar_tools.py
# 3. Update graph/state.py with calendar fields
# 4. Add calendar_agent_node to graph/nodes.py
# 5. Add conditional routing in graph/builder.py
```

### Add Email Templates
```python
# 1. Create tools/email_templates.py
# 2. Store templates in data/templates.json
# 3. Add load_template() tool
# 4. Register with agent
```

### Add Attachment Support
```python
# 1. Update GmailTools.send_email() to accept attachments
# 2. Add base64 encoding logic
# 3. Update send_email() Pydantic tool
# 4. Update system prompt with attachment instructions
```

## Testing Strategy

### Unit Tests
```python
# Test tools independently
async def test_query_database():
    result = await query_email_database(ctx, "John")
    assert "John" in result
```

### Integration Tests
```python
# Test Gmail API integration
def test_gmail_list():
    tools = GmailTools()
    emails = tools.list_emails(max_results=5)
    assert len(emails) <= 5
```

### End-to-End Tests
```python
# Test full conversation flow
async def test_conversation():
    graph = create_graph()
    result = await graph.ainvoke({"user_query": "show unread"})
    assert "agent_response" in result
```

## Logging and Debugging

### Debug Logs
- Location: `logs/langgraph_memory_debug_YYYYMMDD_HHMMSS.log`
- Includes: State transitions, tool calls, memory operations
- Level: DEBUG for development, INFO for production

### Memory Inspection
- Command: `/history` or `/memory` in conversation
- Shows: All messages in current thread
- Format: Role + content + timestamp

### Graph Visualization
- Auto-displayed on startup
- Mermaid format for https://mermaid.live
- Shows: Nodes, edges, conditional routing

## Future Enhancements

- [ ] Attachment upload/download support
- [ ] Email templates with variables
- [ ] Calendar integration (schedule send)
- [ ] Email analytics (stats, insights)
- [ ] Multi-account support
- [ ] Smart reply suggestions
- [ ] Automatic email categorization
- [ ] Natural language date parsing ("next Tuesday")
- [ ] Batch operations (bulk delete, label)
- [ ] Email search filters UI
