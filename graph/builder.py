"""Graph builder for the Gmail conversation system"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from graph.state import GmailState
from graph.nodes import user_input_node, gmail_agent_node, should_continue
from config.settings import INTERRUPT_BEFORE


def create_gmail_graph():
    """Create and compile the LangGraph Gmail system with built-in memory"""
    # Create the graph
    builder = StateGraph(GmailState)

    # Add nodes (bidirectional loop: user_input <-> gmail_agent)
    builder.add_node("user_input", user_input_node)
    builder.add_node("gmail_agent", gmail_agent_node)

    # Add edges
    builder.add_edge(START, "user_input")
    
    # Conditional edge from user_input -> gmail_agent or END
    builder.add_conditional_edges(
        "user_input",
        should_continue,
        {
            "continue": "gmail_agent",
            "end": END
        }
    )
    
    # Conditional edge from gmail_agent -> user_input or END
    builder.add_conditional_edges(
        "gmail_agent",
        should_continue,
        {
            "continue": "user_input",
            "end": END
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

