# Weather Agent Project Structure

This document describes the modular organization of the Weather Agent LangGraph application.

## Directory Structure

```
langgraph_playground/
├── main.py                    # Entry point - run this to start the app
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (API keys)
│
├── agents/                    # AI agent definitions
│   ├── __init__.py
│   └── weather_agent.py      # Pydantic AI weather agent
│
├── graph/                     # LangGraph components
│   ├── __init__.py           # Package exports
│   ├── state.py              # State type definitions
│   ├── nodes.py              # Node function implementations
│   ├── builder.py            # Graph construction logic
│   └── runner.py             # Graph execution and visualization
│
├── tools/                     # Agent tool functions
│   ├── __init__.py
│   ├── location_tools.py     # Location and geocoding tools
│   ├── weather_tools.py      # Weather data fetching tools
│   └── conversation_tools.py # Conversation control tools
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   └── logging.py            # Logging configuration
│
├── config/                    # Configuration settings
│   ├── __init__.py
│   └── settings.py           # Application constants
│
└── logs/                      # Generated log files (gitignored)
    └── langgraph_memory_debug_*.log
```

## Module Responsibilities

### `main.py` - Application Entry Point
- Loads environment variables
- Sets up logging
- Creates and runs the graph
- **Run this file to start the application**

### `graph/` - LangGraph Components

#### `state.py`
- Defines `WeatherState` TypedDict
- Manages conversation state structure

#### `nodes.py`
- `user_input_node()` - Handles user input
- `weather_agent_node()` - Runs the AI agent with tools
- `display_response_node()` - Shows agent responses
- `should_continue()` - Routing logic

#### `builder.py`
- `create_weather_graph()` - Constructs the StateGraph
- Configures edges, checkpointers, and memory

#### `runner.py`
- `run_weather_graph()` - Main execution loop
- `visualize_graph()` - Mermaid diagram generation
- Helper functions for commands and memory display

### `tools/` - Agent Tools
- Weather and location API integrations
- Conversation control functions
- Registered with the Pydantic AI agent

### `utils/` - Utilities
- `logging.py` - Logging setup and configuration

### `config/` - Configuration
- `settings.py` - Application constants and settings

## Running the Application

```bash
# Set up environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Add your API keys to .env file
# OPENAI_API_KEY=your_key_here

# Run the application
python main.py
```

## Adding New Features

### Adding a New Node
1. Add node function to `graph/nodes.py`
2. Import and register in `graph/builder.py`
3. Add edges in `create_weather_graph()`

### Adding a New Tool
1. Create tool function in `tools/`
2. Register with agent in `agent.py`

### Adding Configuration
1. Add constants to `config/settings.py`
2. Import where needed

## Benefits of This Structure

- **Modularity**: Each component has a single responsibility
- **Testability**: Individual modules can be tested in isolation
- **Scalability**: Easy to add new nodes, tools, or graphs
- **Maintainability**: Clear separation of concerns
- **Reusability**: Components can be reused in other projects

