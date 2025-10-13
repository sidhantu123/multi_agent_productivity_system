"""Node functions for the Gmail conversation graph"""

from graph.state import GmailState
from agents.gmail_agent import get_gmail_agent, get_gmail_tools
from tools.gmail_tools import GmailDeps
from utils.logging import get_logger

logger = get_logger()


async def user_input_node(state: GmailState) -> dict:
    """Get user input for the Gmail query - LangGraph handles memory automatically"""
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


async def gmail_agent_node(state: GmailState) -> dict:
    """Run the Gmail agent - LangGraph handles memory automatically"""
    user_query = state["user_query"]
    
    # Log state for debugging
    logger.debug(f"GMAIL_AGENT_NODE - Current state keys: {list(state.keys())}")
    logger.debug(f"GMAIL_AGENT_NODE - User query: {user_query}")
    logger.debug(f"GMAIL_AGENT_NODE - Existing messages: {state.get('messages', [])}")
    
    # Check conversation history for context
    existing_messages = state.get("messages", [])
    if existing_messages:
        logger.info(f"Agent has {len(existing_messages)} messages in memory for context")
    else:
        logger.info("No conversation history available - agent starting fresh")

    print(f"\nProcessing: {user_query}")

    try:
        # Get Gmail tools instance
        gmail_tools = get_gmail_tools()
        
        # Create dependencies with email context and Gmail service
        deps = GmailDeps(
            emails=state.get('emails', []),
            gmail_service=gmail_tools
        )
        
        # Build conversation context
        conversation_context = user_query
        if existing_messages:
            context_parts = []
            for msg in existing_messages[-5:]:  # Last 5 messages for context
                role = None
                content = None
                if isinstance(msg, dict):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                else:
                    try:
                        role = getattr(msg, "type", None) or getattr(msg, "role", None) or "assistant"
                        content = getattr(msg, "content", None) or str(msg)
                    except Exception:
                        role = "assistant"
                        content = str(msg)
                context_parts.append(f"{role}: {content}")
            
            if context_parts:
                conversation_context = "Previous conversation:\n" + "\n".join(context_parts) + "\n\nCurrent question: " + user_query

        # Run the Pydantic AI agent with conversation context and event streaming
        from pydantic_ai.messages import AgentStreamEvent, FunctionToolCallEvent
        from collections.abc import AsyncIterable
        
        agent = get_gmail_agent()
        
        # Track tool calls and end_conversation
        tool_calls = []
        end_conversation_called = False
        
        print()  # New line before tool calls
        
        # Event handler to print tool calls in real-time
        async def stream_handler(ctx, event_stream: AsyncIterable[AgentStreamEvent]):
            nonlocal end_conversation_called
            async for event in event_stream:
                if isinstance(event, FunctionToolCallEvent):
                    tool_name = event.part.tool_name
                    tool_calls.append(tool_name)
                    print(f"Calling tool: {tool_name}()")
                    
                    # Check if end_conversation tool was called
                    if tool_name == 'end_conversation':
                        end_conversation_called = True
        
        # Run agent with event streaming
        result = await agent.run(conversation_context, deps=deps, event_stream_handler=stream_handler)
        
        response = result.output
        
        # Log the response
        logger.info(f"Agent response: {response}")
        logger.debug(f"Tool calls made: {tool_calls}")
        
        # Display the response
        print(f"\nAnswer: {response}\n")
        
        # Update emails in state from deps (deps are modified in place)
        emails_update = {}
        if deps.emails:
            emails_update['emails'] = deps.emails

        return {
            "agent_response": response,
            "messages": [{"role": "assistant", "content": str(response)}],
            "continue_conversation": not end_conversation_called,
            **emails_update
        }
        
    except Exception as e:
        error_msg = f"Error processing Gmail query: {str(e)}"
        logger.error(error_msg)
        return {
            "agent_response": error_msg,
            "messages": [{"role": "assistant", "content": error_msg}],
            "continue_conversation": True
        }


def should_continue(state: GmailState) -> str:
    """Determine if conversation should continue"""
    if state.get("continue_conversation", True):
        return "continue"
    return "end"

