# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Multi-Agent Productivity System built with LangGraph and Pydantic AI, featuring Gmail and Google Calendar agents. The system currently includes:

- **Gmail Agent**: Full LangGraph integration with stateful conversations
- **Calendar Agent**: Standalone Pydantic AI agent with comprehensive calendar operations
- **Shared Infrastructure**: Contact database, conversation tools, and Google API integrations
- **Future**: Orchestrator agent to route between Gmail and Calendar agents

## Current System Architecture

### Agents
- **Gmail Agent** (`agents/gmail_agent.py`): Email management with 22 tools
- **Calendar Agent** (`agents/calendar_agent.py`): Calendar operations with 12 tools
- **Shared Tools**: Database (7 tools), conversation (2 tools)

### Entry Points
- `main.py`: Gmail agent with LangGraph orchestration
- `test_calendar.py`: Standalone Calendar agent CLI for testing
- `graph_visualization.py`: Mermaid diagram generation for graph structure

### Key Technologies
- **Orchestration**: LangGraph for stateful conversations (Gmail agent)
- **AI Framework**: Pydantic AI with OpenAI GPT-4o-mini
- **APIs**: Google Gmail API, Google Calendar API
- **Database**: TinyDB for contact caching
- **Auth**: Google OAuth 2.0

## Development Setup

### Python Environment
- Use Python virtual environments: `python -m venv venv` then `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Set up environment variables in `.env` (OPENAI_API_KEY)

### Authentication Setup
1. **Google Cloud Project**: Enable Gmail and Calendar APIs
2. **OAuth Credentials**: Download desktop app credentials as `config/google_credentials.json`
3. **First Run**: Authenticate via browser for Gmail and Calendar tokens

### Running the System

#### Gmail Agent (LangGraph)
```bash
python main.py
```

#### Calendar Agent (Standalone)
```bash
python test_calendar.py
```

#### Graph Visualization
```bash
python graph_visualization.py
```

## Code Organization

### Modular Tool Structure
- **One tool per file**: Each tool in its own file for maintainability
- **Service classes**: `GmailTools` and `CalendarTools` for API operations
- **Dependency injection**: `GmailDeps` and `CalendarDeps` for context
- **Centralized exports**: All tools exported via `__init__.py` files

### Key Directories
- `agents/`: Agent definitions with system prompts and tool registration
- `tools/`: Modular tool implementations (gmail_tools/, calendar_tools/, database_tools/, conversation_tools/)
- `graph/`: LangGraph components for Gmail agent (state, nodes, builder, runner)
- `config/`: OAuth credentials and application settings
- `data/`: TinyDB contact cache

## Development Guidelines

### Adding New Tools
1. Add method to service class (`GmailTools` or `CalendarTools`)
2. Create tool wrapper file in appropriate `tools/` subdirectory
3. Export tool in `__init__.py`
4. Register tool in agent definition (`gmail_agent.py` or `calendar_agent.py`)
5. Update system prompt if needed

### Adding New Agents
1. Create agent definition in `agents/`
2. Create tool directory structure in `tools/`
3. Implement service class and dependency injection
4. Create standalone test CLI
5. Plan LangGraph integration for unified system

### System Prompt Guidelines
- Define agent identity and capabilities clearly
- Include user context (name, email, timezone for Calendar)
- Specify tool usage patterns and workflows
- Add timezone handling and API format requirements
- Include examples for complex operations

## LangGraph Integration (Gmail Agent)

### Current Implementation
- **State Management**: `GmailState` with conversation history and email cache
- **Node Functions**: User input processing, agent execution, response display
- **Memory**: Built-in conversation persistence with `MemorySaver`
- **Routing**: Conditional edges based on conversation flow

### Future Orchestration
- **Multi-Agent Routing**: Intent-based routing between Gmail and Calendar
- **Cross-Agent Workflows**: Email → calendar event creation
- **Unified State**: Shared context across agents
- **Orchestrator Agent**: Central routing and coordination

## Testing and Debugging

### Agent Testing
- **Gmail Agent**: Full LangGraph conversation loop with memory
- **Calendar Agent**: Standalone CLI with Pydantic AI memory
- **Tool Testing**: Individual tool functions with mock dependencies

### Debugging Tools
- **Logging**: Comprehensive logging in `utils/logging.py`
- **Graph Visualization**: Mermaid diagrams via `graph_visualization.py`
- **Memory Inspection**: Built-in conversation history commands

### Common Issues
- **Authentication**: Delete tokens and re-authenticate if scopes change
- **API Errors**: Check Google Cloud project API enablement
- **Memory Issues**: LangGraph memory vs Pydantic AI memory differences
- **Timezone**: PST context for Calendar agent, UTC for API calls

## Future Development

### Planned Features
- **Orchestrator Agent**: Intent-based routing between Gmail and Calendar
- **LangGraph Integration**: Calendar agent integration into unified graph
- **Cross-Agent Workflows**: Email thread → calendar event
- **Enhanced Memory**: Shared context across agents
- **Multi-Agent Conversations**: Coordinated responses

### Architecture Evolution
```
Current: Gmail (LangGraph) + Calendar (Standalone)
Future: Orchestrator → [Gmail Agent, Calendar Agent] (Both in LangGraph)
```

## Logs Directory

The `logs/` directory contains MCP (Model Context Protocol) server logs and should not be committed to version control.