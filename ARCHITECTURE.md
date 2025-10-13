# Weather Agent Architecture

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
│WeatherS │ │ Node    │ │ Exec    │
│tate     │ │ Funcs   │ │ Loop    │
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
          │ • location  │
          │ • weather   │
          │ • convers.  │
          └─────────────┘
```

## Component Flow

### 1. **Startup Flow**
```
main.py
  ├─> load_dotenv()
  ├─> setup_logging()
  ├─> create_weather_graph()
  │     ├─> Create StateGraph
  │     ├─> Add nodes (from nodes.py)
  │     ├─> Add edges
  │     └─> Compile with memory
  └─> run_weather_graph()
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
weather_agent_node (graph/nodes.py)
  ├─> Build conversation context
  ├─> Call get_weather_agent() (agent.py)
  │     ├─> Create agent (lazy init)
  │     ├─> Register tools (tools/)
  │     └─> Run with context
  ├─> Process tool calls
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
  ├─> Thread ID: weather_conversation_1
  └─> Messages persisted automatically
```

## Module Dependencies

```
main.py
  ├── utils.logging
  ├── graph.builder
  └── graph.runner
        ├── graph.state
        ├── graph.nodes
        │     ├── agent (lazy)
        │     └── tools
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
│ WeatherState │ ◄──┐
│ (graph/state)│    │
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
┌──────────────┐   │
│   Response   │───┘
└──────────────┘
```

## Design Patterns Used

1. **Separation of Concerns**: Each module has one responsibility
2. **Dependency Injection**: Tools injected into agent
3. **Lazy Initialization**: Agent created only when needed
4. **Factory Pattern**: `create_weather_graph()`, `create_weather_agent()`
5. **State Machine**: LangGraph StateGraph pattern
6. **Observer Pattern**: Event streaming in runner

## Extension Points

### Adding a New Node
```python
# 1. Define in graph/nodes.py
async def my_new_node(state: WeatherState) -> dict:
    # logic here
    return updated_state

# 2. Register in graph/builder.py
builder.add_node("my_node", my_new_node)
builder.add_edge("previous_node", "my_node")
```

### Adding a New Tool
```python
# 1. Create in tools/my_tool.py
async def my_tool(ctx: RunContext[Deps]) -> str:
    return "result"

# 2. Register in agent.py
agent.tool(my_tool)
```

### Adding Configuration
```python
# 1. Add to config/settings.py
MY_SETTING = "value"

# 2. Import where needed
from config.settings import MY_SETTING
```

## Benefits of This Architecture

- ✅ **Testable**: Mock any component
- ✅ **Maintainable**: Clear file boundaries
- ✅ **Scalable**: Easy to extend
- ✅ **Debuggable**: Isolated concerns
- ✅ **Reusable**: Components work independently
- ✅ **Professional**: Industry best practices

