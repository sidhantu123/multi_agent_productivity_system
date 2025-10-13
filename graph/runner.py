"""Graph execution and visualization logic"""

import os
from graph.state import GmailState
from config.settings import THREAD_ID, SEPARATOR_LENGTH, MEMORY_SEPARATOR_LENGTH
from utils.logging import get_logger

logger = get_logger()


async def visualize_graph(graph):
    """Visualize the graph using Mermaid"""
    print("\n" + "="*SEPARATOR_LENGTH)
    print("Graph Visualization (Mermaid)")
    print("="*SEPARATOR_LENGTH)
    try:
        mermaid_code = graph.get_graph().draw_mermaid()
        print(mermaid_code)
        print("\nCopy the above code to https://mermaid.live to visualize the graph")
    except Exception as e:
        print(f"Could not generate Mermaid visualization: {e}")
    print("="*SEPARATOR_LENGTH + "\n")


async def run_gmail_graph(graph):
    """Run the Gmail graph system"""
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY not found in environment variables")
        print("Please set it in your .env file or environment")
        return

    # Visualize the graph
    await visualize_graph(graph)

    # Initial state - LangGraph handles memory automatically
    initial_state: GmailState = {
        "messages": [],
        "user_query": "",
        "agent_response": "",
        "continue_conversation": True,
        "emails": None,
        "selected_email_id": None,
        "email_action": None
    }

    # Configuration for the graph
    config = {
        "configurable": {
            "thread_id": THREAD_ID
        }
    }

    print("Starting Gmail Agent Graph...")
    print("Tip: The graph will pause for your input at each turn")
    print("Memory: Using LangGraph's built-in memory features")
    print("Commands: Type /help for available commands\n")
    print("="*SEPARATOR_LENGTH)
    print("Gmail Agent - LangGraph Edition with Built-in Memory")
    print("="*SEPARATOR_LENGTH)

    try:
        # Start the graph
        state = None
        logger.info("Starting graph execution with memory debugging")

        while True:
            # Log current state before processing
            if state:
                logger.debug(f"Current state before processing: {list(state.keys())}")
                logger.debug(f"Messages in state: {state.get('messages', [])}")
            
            # Run the graph until it hits an interrupt
            events = []
            logger.debug("Running graph stream...")
            async for event in graph.astream(initial_state if state is None else None, config, stream_mode="values"):
                events.append(event)
                state = event
                logger.debug(f"Event received: {list(event.keys()) if isinstance(event, dict) else type(event)}")

            # Log final state
            if state:
                logger.info(f"Final state after graph run: {list(state.keys())}")
                logger.info(f"Messages in final state: {len(state.get('messages', []))} messages")
                for i, msg in enumerate(state.get('messages', [])):
                    logger.debug(f"Message {i}: {msg}")

            # Check if we've reached the end
            if state and not state.get("continue_conversation", True):
                print("\nGoodbye!")
                break

            # Check for interrupt
            snapshot = graph.get_state(config)
            logger.debug(f"Snapshot next: {snapshot.next}")
            logger.debug(f"Snapshot values: {list(snapshot.values.keys()) if snapshot.values else 'None'}")
            
            if snapshot.next:  # Graph is waiting at an interrupt
                # Get user input
                user_input = input("\nYou: ").strip()
                logger.info(f"User input: {user_input}")

                if not user_input:
                    continue

                # Handle special memory commands using LangGraph's built-in features
                if user_input.lower() in ["/help", "/commands"]:
                    _display_help()
                    continue
                
                if user_input.lower() in ["/history", "/memory", "/context"]:
                    _display_memory(snapshot, config)
                    continue

                # Resume the graph with user input (also append to messages for memory)
                logger.info(f"Updating state with user input: {user_input}")
                logger.debug(f"Config: {config}")
                graph.update_state(
                    config,
                    {
                        "user_query": user_input,
                        "messages": [{"role": "user", "content": user_input}],
                    },
                    as_node="user_input",
                )
                logger.info("State updated successfully")
            else:
                # No more interrupts, end the conversation
                break

    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


def _display_help():
    """Display help information"""
    print("\n" + "="*MEMORY_SEPARATOR_LENGTH)
    print("GMAIL AGENT COMMANDS")
    print("="*MEMORY_SEPARATOR_LENGTH)
    print("Available commands:")
    print("  /history, /memory, /context - Show conversation memory")
    print("  /help, /commands - Show this help")
    print("  quit, exit, q - End conversation")
    print("\nLangGraph Memory Features:")
    print("  Automatic conversation memory (MemorySaver)")
    print("  Long-term memory storage (InMemoryStore)")
    print("  State persistence across sessions")
    print("  Built-in checkpointing and recovery")
    print("="*MEMORY_SEPARATOR_LENGTH + "\n")


def _display_memory(snapshot, config):
    """Display conversation memory"""
    current_state = snapshot.values
    logger.info("Memory command triggered - displaying conversation history")
    logger.debug(f"Current state from snapshot: {list(current_state.keys()) if current_state else 'None'}")
    
    print("\n" + "="*MEMORY_SEPARATOR_LENGTH)
    print("LANGGRAPH CONVERSATION MEMORY")
    print("="*MEMORY_SEPARATOR_LENGTH)
    
    # Display messages from LangGraph's built-in memory
    if current_state and current_state.get("messages"):
        logger.info(f"Found {len(current_state['messages'])} messages in memory")
        print("Conversation History (from LangGraph memory):")
        for i, msg in enumerate(current_state["messages"], 1):
            if isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                print(f"  {i}. {role.upper()}: {content}")
                logger.debug(f"Message {i}: {role} - {content[:50]}...")
            else:
                print(f"  {i}. {msg}")
                logger.debug(f"Message {i}: {str(msg)[:50]}...")
    else:
        logger.warning("No messages found in current state")
        print("No conversation history found")
    
    # Show thread information
    print(f"\nThread ID: {config['configurable']['thread_id']}")
    print(f"State Keys: {list(current_state.keys()) if current_state else 'None'}")
    
    print("="*MEMORY_SEPARATOR_LENGTH + "\n")

