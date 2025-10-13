"""Node functions for the weather conversation graph"""

import httpx
from graph.state import WeatherState
from agents import get_weather_agent
from tools.location_tools import WeatherDeps
from utils.logging import get_logger

logger = get_logger()


async def user_input_node(state: WeatherState) -> dict:
    """Get user input for the weather query - LangGraph handles memory automatically"""
    user_query = state.get("user_query", "")
    
    # Log current state for debugging
    logger.debug(f"USER_INPUT_NODE - Current state keys: {list(state.keys())}")
    logger.debug(f"USER_INPUT_NODE - User query: {user_query}")
    logger.debug(f"USER_INPUT_NODE - Existing messages: {state.get('messages', [])}")
    
    # Check if we have conversation history
    existing_messages = state.get("messages", [])
    if existing_messages:
        logger.info(f"Found {len(existing_messages)} existing messages in memory")
        for i, msg in enumerate(existing_messages):
            logger.debug(f"Message {i}: {msg}")
    else:
        logger.info("No existing messages found - starting fresh conversation")

    return {
        "user_query": user_query,
        "continue_conversation": True,
        "messages": [{"role": "user", "content": user_query}]
    }


async def weather_agent_node(state: WeatherState) -> dict:
    """Run the Pydantic AI weather agent - LangGraph handles memory automatically"""
    user_query = state["user_query"]
    
    # Log state for debugging
    logger.debug(f"WEATHER_AGENT_NODE - Current state keys: {list(state.keys())}")
    logger.debug(f"WEATHER_AGENT_NODE - User query: {user_query}")
    logger.debug(f"WEATHER_AGENT_NODE - Existing messages: {state.get('messages', [])}")
    
    # Check conversation history for context
    existing_messages = state.get("messages", [])
    if existing_messages:
        logger.info(f"Agent has {len(existing_messages)} messages in memory for context")
        # Log recent conversation context
        recent_messages = existing_messages[-3:] if len(existing_messages) >= 3 else existing_messages
        logger.debug(f"Recent conversation context: {recent_messages}")
    else:
        logger.info("No conversation history available - agent starting fresh")

    print(f"\nProcessing: {user_query}")

    # Create a new HTTP client for this node
    async with httpx.AsyncClient() as http_client:
        # Create dependencies for the agent
        deps = WeatherDeps(http_client=http_client)

        # Build conversation context for the agent
        conversation_context = ""
        if existing_messages:
            # Create a conversation context string supporting dict and LangChain messages
            context_parts = []
            for msg in existing_messages[-5:]:  # Last 5 messages for context
                role = None
                content = None
                if isinstance(msg, dict):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                else:
                    # Likely a LangChain Message (AIMessage/HumanMessage)
                    try:
                        role = getattr(msg, "type", None) or getattr(msg, "role", None) or "assistant"
                        content = getattr(msg, "content", None) or str(msg)
                    except Exception:
                        role = "assistant"
                        content = str(msg)
                context_parts.append(f"{role}: {content}")
            
            if context_parts:
                conversation_context = "Previous conversation:\n" + "\n".join(context_parts) + "\n\nCurrent question: " + user_query
                logger.info(f"Passing conversation context to agent: {len(conversation_context)} characters")
            else:
                conversation_context = user_query
        else:
            conversation_context = user_query
            logger.info("No conversation history - passing user query directly")

        # Run the Pydantic AI agent with conversation context
        agent = get_weather_agent()
        result = await agent.run(conversation_context, deps=deps)

        # Trace tool calls and check for end_conversation
        print("\nTool Calls:")
        tool_calls = []
        end_conversation_called = False

        for message in result.new_messages():
            if hasattr(message, 'parts'):
                for part in message.parts:
                    if hasattr(part, 'tool_name'):
                        tool_calls.append(part.tool_name)
                        print(f"   - {part.tool_name}()")

                        # Check if end_conversation tool was called
                        if part.tool_name == 'end_conversation':
                            end_conversation_called = True

        response = result.output
        
        # Log the response
        logger.info(f"Agent response: {response}")
        logger.debug(f"Tool calls made: {tool_calls}")

        return {
            "agent_response": response,
            "messages": [{"role": "assistant", "content": str(response)}],
            "continue_conversation": not end_conversation_called
        }


async def display_response_node(state: WeatherState) -> dict:
    """Display the agent's response - LangGraph handles memory display"""
    print(f"\nAnswer: {state['agent_response']}\n")

    # Return the state as-is, preserving continue_conversation flag
    return state


def should_continue(state: WeatherState) -> str:
    """Determine if conversation should continue"""
    if state.get("continue_conversation", True):
        return "continue"
    return "end"

