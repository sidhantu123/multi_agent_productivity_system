"""Graph builder for the multi-agent conversation system"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from graph.state import UnifiedState
from graph.nodes import (
    user_input_node,
    orchestrator_node,
    gmail_agent_node,
    calendar_agent_node,
    should_continue,
    route_to_agent
)
from config.settings import INTERRUPT_BEFORE


def create_graph():
    """Create and compile the LangGraph multi-agent system with orchestrator routing using Command"""
    # Create the graph
    builder = StateGraph(UnifiedState)

    # Add nodes (flow: user_input -> orchestrator -> [gmail_agent | calendar_agent])
    # Agents now use Command to route dynamically, so no conditional edges needed
    builder.add_node("user_input", user_input_node)
    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("gmail_agent", gmail_agent_node)
    builder.add_node("calendar_agent", calendar_agent_node)

    # Add edges
    builder.add_edge(START, "user_input")

    # Conditional edge from user_input -> orchestrator or END
    builder.add_conditional_edges(
        "user_input",
        should_continue,
        {
            "continue": "orchestrator",
            "end": END
        }
    )

    # Conditional edge from orchestrator -> gmail_agent or calendar_agent
    builder.add_conditional_edges(
        "orchestrator",
        route_to_agent,
        {
            "gmail_agent": "gmail_agent",
            "calendar_agent": "calendar_agent"
        }
    )

    # No edges from gmail_agent or calendar_agent - they use Command to route dynamically!
    # Command pattern allows agents to decide their own routing:
    # - gmail_agent can route to: calendar_agent (if agent_type="both"), user_input, or END
    # - calendar_agent can route to: user_input or END

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

