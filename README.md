# Weather Agent - LangGraph Edition

A modular, production-ready weather chatbot built with LangGraph and Pydantic AI. Features conversation memory, tool calling, and a clean architectural design.

## Features

- 🤖 **AI-Powered**: Uses OpenAI GPT-4o with Pydantic AI
- 🧠 **Conversation Memory**: LangGraph's built-in memory system remembers context
- 🌍 **Location-Aware**: Automatic location detection via IP
- 🌤️ **Real-time Weather**: Fetches current weather data
- 🔧 **Tool Calling**: Agent can call multiple weather and location tools
- 📊 **Graph Visualization**: Mermaid diagrams of conversation flow
- 🏗️ **Modular Architecture**: Clean, scalable codebase

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key

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

### Running the Application

```bash
python main.py
```

## Project Structure

```
langgraph_playground/
├── main.py                    # Entry point
├── agents/                    # AI agent definitions
│   └── weather_agent.py      # Pydantic AI weather agent
├── graph/                     # LangGraph components
│   ├── state.py              # State definitions
│   ├── nodes.py              # Node functions
│   ├── builder.py            # Graph construction
│   └── runner.py             # Execution logic
├── tools/                     # Agent tools
│   ├── location_tools.py     # Location & geocoding
│   ├── weather_tools.py      # Weather data fetching
│   └── conversation_tools.py # Conversation control
├── utils/                     # Utilities
│   └── logging.py            # Logging configuration
└── config/                    # Configuration
    └── settings.py           # Application constants
```

## Usage

### Basic Conversation

```
You: What's the weather like?
Answer: The current weather in Westminster, California is 60.2°F...

You: How about in San Francisco?
Answer: The weather in San Francisco is 58°F...

You: What did I just ask you?
Answer: You asked about the weather in San Francisco.
```

### Commands

- `/help` - Show available commands
- `/history` - View conversation memory
- `/memory` - Same as /history
- `/context` - Same as /history
- `quit` - Exit the application

## Architecture

### LangGraph Flow

```
START → user_input → weather_agent → display_response → user_input (loop)
```

### Memory System

- **MemorySaver**: Automatic conversation state persistence
- **InMemoryStore**: Long-term memory across sessions
- **Thread-based**: Isolated conversation threads
- **Message Accumulation**: Built-in message history tracking

### Agent Tools

- `get_user_location()` - IP-based location detection
- `get_lat_long()` - City to coordinates conversion
- `convert_address_to_lat_long()` - Address geocoding
- `get_weather()` - Current weather data
- `end_conversation()` - Graceful conversation exit

## Development

### Adding a New Node

```python
# 1. Define in graph/nodes.py
async def my_node(state: WeatherState) -> dict:
    # Your logic here
    return updated_state

# 2. Register in graph/builder.py
builder.add_node("my_node", my_node)
builder.add_edge("previous_node", "my_node")
```

### Adding a New Tool

```python
# 1. Create in tools/my_tool.py
async def my_tool(ctx: RunContext[Deps]) -> str:
    return "result"

# 2. Register in agents/weather_agent.py
weather_agent.tool(my_tool)
```

## Documentation

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Detailed structure guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and diagrams

## Technologies

- **LangGraph** - Conversation orchestration
- **Pydantic AI** - AI agent framework
- **OpenAI GPT-4o** - Language model
- **Open-Meteo API** - Weather data
- **IP-API** - Geolocation

## License

MIT

## Author

Sidhant Umbrajkar

