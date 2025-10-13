"""Graph builder for the weather conversation system"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from graph.state import WeatherState
from graph.nodes import user_input_node, weather_agent_node, display_response_node, should_continue
from config.settings import INTERRUPT_BEFORE


def create_weather_graph():
    """Create and compile the LangGraph weather system with built-in memory"""
    # Create the graph
    builder = StateGraph(WeatherState)

    # Add nodes
    builder.add_node("user_input", user_input_node)
    builder.add_node("weather_agent", weather_agent_node)
    builder.add_node("display_response", display_response_node)

    # Add edges
    builder.add_edge(START, "user_input")
    builder.add_edge("weather_agent", "display_response")

    # Add conditional edges
    builder.add_conditional_edges(
        "user_input",
        should_continue,
        {
            "continue": "weather_agent",
            "end": END
        }
    )

    builder.add_conditional_edges(
        "display_response",
        lambda x: "continue",  # Always go back to user input
        {
            "continue": "user_input"
        }
    )

    # Compile with LangGraph's built-in memory features
    # MemorySaver handles conversation memory automatically
    # InMemoryStore can be used for long-term memory if needed
    memory_saver = MemorySaver()
    store = InMemoryStore()  # For long-term memory across sessions
    
    graph = builder.compile(
        checkpointer=memory_saver,  # Handles conversation memory
        store=store,  # Handles long-term memory
        interrupt_before=INTERRUPT_BEFORE
    )

    return graph

