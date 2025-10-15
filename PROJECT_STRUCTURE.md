# Multi-Agent Productivity System Project Structure

This document describes the modular organization of the Multi-Agent Productivity System built with LangGraph and Pydantic AI, featuring Gmail and Calendar agents.

## Directory Structure

```
langgraph_playground/
├── main.py                          # Entry point - Gmail agent with LangGraph
├── test_calendar.py                 # Standalone Calendar agent CLI test
├── graph_visualization.py           # Standalone graph visualization utility
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (OPENAI_API_KEY)
│
├── agents/                          # AI agent definitions
│   ├── __init__.py
│   ├── gmail_agent.py               # Pydantic AI Gmail agent with tool registration
│   └── calendar_agent.py            # Pydantic AI Calendar agent (standalone for now)
│
├── graph/                           # LangGraph components (Gmail agent only)
│   ├── __init__.py                  # Package exports
│   ├── state.py                     # UnifiedState type definition
│   ├── nodes.py                     # Node function implementations
│   ├── builder.py                   # Graph construction logic
│   └── runner.py                    # Graph execution and visualization
│
├── tools/                           # Agent tool functions (modular structure)
│   ├── __init__.py
│   ├── gmail_tools/                 # Gmail operations (22 files)
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
│   ├── calendar_tools/              # Google Calendar operations (12 files)
│   │   ├── __init__.py              # Exports all Calendar tools
│   │   ├── core.py                  # CalendarTools service class & CalendarDeps
│   │   ├── list_events.py           # List upcoming events
│   │   ├── get_event.py             # Get event details
│   │   ├── create_event.py          # Create new event
│   │   ├── update_event.py          # Modify time/details
│   │   ├── manage_attendees.py      # Add/remove attendees
│   │   ├── delete_event.py          # Delete event
│   │   ├── update_rsvp.py           # RSVP updates
│   │   ├── get_current_time.py      # Current date/time tool
│   │   ├── add_google_meet.py       # Add Meet / create event with Meet
│   │   └── set_reminders.py         # Configure event reminders
│   ├── database_tools/              # Contact database (7 files)
│   │   ├── __init__.py              # Exports all database tools
│   │   ├── db.py                    # TinyDB utilities
│   │   ├── query_database.py        # Query contacts
│   │   ├── add_contact.py           # Add contact
│   │   ├── check_human_sender.py    # Detect human vs automated
│   │   ├── list_contacts.py         # List all contacts
│   │   └── remove_contact.py        # Remove contact
│   └── conversation_tools/          # Conversation control (2 files)
│       ├── __init__.py              # Exports conversation tools
│       └── end_conversation.py      # End conversation tool
│
├── utils/                           # Utility functions
│   ├── __init__.py
│   └── logging.py                   # Logging configuration
│
├── config/                          # Configuration settings
│   ├── __init__.py
│   ├── settings.py                  # Application constants
│   ├── google_credentials.json      # OAuth 2.0 client credentials (user provided)
│   ├── google_token.json            # Gmail auth token (gitignored)
│   └── google_calendar_token.json   # Calendar auth token (gitignored)
│
├── data/                            # Data storage (gitignored)
│   └── email_contacts.json          # TinyDB contact cache
│
├── logs/                            # Generated log files (gitignored)
│   └── [various log files]
│
└── .claude/                         # Claude IDE configuration
    ├── CLAUDE.md                    # Development guidelines
    └── settings.local.json          # Local settings
```

## Module Responsibilities

### Entry Points

#### `main.py` - Gmail Agent Entry Point
- Loads environment variables from `.env`
- Sets up logging configuration
- Creates the Gmail LangGraph
- Runs the main conversation loop
- **Run this file to start the Gmail agent with LangGraph**

#### `test_calendar.py` - Calendar Agent CLI Test
- Standalone CLI for testing Calendar agent
- Uses Pydantic AI's built-in memory system
- Direct agent interaction without LangGraph
- **Run this file to test Calendar agent functionality**

#### `graph_visualization.py` - Graph Visualization Utility
- Generates Mermaid diagrams of the Gmail agent graph
- Standalone utility for understanding graph structure
- **Run this file to visualize the LangGraph structure**

### `agents/` - AI Agent Definitions

#### `gmail_agent.py`
- Creates Pydantic AI agent with OpenAI GPT-4o-mini
- Defines comprehensive system prompt with:
  - Agent identity (Sidhant Umbrajkar's assistant)
  - Email address lookup strategy
  - New sender detection workflow
  - Draft vs send logic
  - Gmail search syntax guidance
- Registers all Gmail and database tools
- Exports `create_gmail_agent()`, `get_gmail_agent()`, `get_gmail_tools()`

#### `calendar_agent.py`
- Creates Pydantic AI agent with OpenAI GPT-4o-mini
- Defines comprehensive system prompt with:
  - Agent identity (Sidhant Umbrajkar's Calendar assistant)
  - PST timezone context and conversion
  - Google Meet integration
  - RSVP status management
  - Event notification configuration
- Registers all Calendar, database, and conversation tools
- Exports `create_calendar_agent()`, `get_calendar_agent()`, `get_calendar_tools()`

### `graph/` - LangGraph Components (Gmail Agent Only)

#### `state.py`
- Defines `UnifiedState` TypedDict with fields:
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
- **`create_graph()`**:
  - Creates `StateGraph(UnifiedState)`
  - Adds all nodes from `nodes.py`
  - Defines edges and routing logic
  - Compiles with `MemorySaver` for conversation persistence
  - Returns compiled graph ready for execution

#### `runner.py`
- **`run_gmail_graph()`**:
  - Handles graph execution and user interaction
  - Manages conversation loop
  - Handles graceful shutdown

### `tools/` - Agent Tool Functions

#### `gmail_tools/` - Gmail Operations (22 files)
- **`core.py`**: `GmailTools` service class and `GmailDeps` for dependency injection
- **Viewing**: `list_emails.py`, `read_email.py`, `get_unread.py`, `search_emails.py`
- **Modification**: `mark_read.py`, `mark_unread.py`, `archive_email.py`, `trash_email.py`, `delete_email.py`
- **Labels**: `get_labels.py`, `create_label.py`, `delete_label.py`, `add_label.py`, `remove_label.py`
- **Composition**: `send_email.py`, `reply_to_email.py`, `create_draft.py`, `create_draft_reply.py`
- **Utilities**: `find_email_address.py`, `unsubscribe.py`
- **`__init__.py`**: Exports all Gmail tools for agent registration

#### `calendar_tools/` - Google Calendar Operations (12 files)
- **`core.py`**: `CalendarTools` service class and `CalendarDeps` for dependency injection
- **Viewing**: `list_events.py`, `get_event.py`
- **Creation**: `create_event.py`
- **Modification**: `update_event.py`, `manage_attendees.py`, `update_rsvp.py`, `set_reminders.py`
- **Google Meet**: `add_google_meet.py`
- **Utilities**: `get_current_time.py`, `delete_event.py`
- **`__init__.py`**: Exports all Calendar tools for agent registration

#### `database_tools/` - Contact Database (7 files)
- **`core.py`**: TinyDB utilities and database management
- **Operations**: `query_database.py`, `add_contact.py`, `list_contacts.py`, `remove_contact.py`
- **Utilities**: `check_human_sender.py`
- **`__init__.py`**: Exports all database tools for agent registration

#### `conversation_tools/` - Conversation Control (2 files)
- **`end_conversation.py`**: Graceful conversation termination
- **`__init__.py`**: Exports conversation tools

### `utils/` - Utility Functions

#### `logging.py`
- Configures Python logging for the application
- Sets up console and file logging
- Configures log levels and formats

### `config/` - Configuration Settings

#### `settings.py`
- Application constants and configuration
- API endpoints and service settings

#### Authentication Files
- **`google_credentials.json`**: OAuth 2.0 client credentials (user provided)
- **`google_token.json`**: Gmail authentication token (gitignored)
- **`google_calendar_token.json`**: Calendar authentication token (gitignored)

### `data/` - Data Storage

#### `email_contacts.json`
- TinyDB contact cache for fast email lookups
- Stores contact information learned from email interactions

## Architecture Patterns

### Multi-Agent System
- **Gmail Agent**: Integrated with LangGraph for stateful conversations
- **Calendar Agent**: Standalone Pydantic AI agent for testing and development
- **Shared Tools**: Database and conversation tools used by both agents
- **Future**: Orchestrator agent to route between Gmail and Calendar

### Modular Tool Organization
- One tool per file for maintainability
- Service classes (`GmailTools`, `CalendarTools`) for API operations
- Dependency injection with `GmailDeps` and `CalendarDeps`
- Centralized exports via `__init__.py` files

### Memory Systems
- **LangGraph Memory**: Conversation persistence for Gmail agent
- **Pydantic AI Memory**: Built-in message history for Calendar agent
- **TinyDB Cache**: Contact database for both agents

## Current Status

### Implemented
- ✅ Gmail agent with full LangGraph integration
- ✅ Calendar agent with standalone CLI
- ✅ Comprehensive tool sets for both agents
- ✅ Shared contact database system
- ✅ Google Meet integration
- ✅ Event notification/reminder system
- ✅ PST timezone context for Calendar agent

### In Progress
- 🔄 Calendar agent integration into LangGraph architecture
- 🔄 Orchestrator agent for multi-agent routing

### Future Enhancements
- 📋 Unified multi-agent system with LangGraph
- 📋 Intent-based routing between Gmail and Calendar
- 📋 Cross-agent workflows (e.g., email → calendar event)
- 📋 Enhanced memory sharing between agents

## Development Guidelines

### Adding New Tools
1. Add method to service class (`GmailTools` or `CalendarTools`)
2. Create tool wrapper file in appropriate `tools/` subdirectory
3. Export tool in `__init__.py`
4. Register tool in agent definition
5. Update system prompt if needed

### Adding New Agents
1. Create agent definition in `agents/`
2. Create tool directory structure
3. Implement service class and dependency injection
4. Create standalone test CLI
5. Plan LangGraph integration

### Testing
- **Gmail Agent**: `python main.py`
- **Calendar Agent**: `python test_calendar.py`
- **Graph Visualization**: `python graph_visualization.py`