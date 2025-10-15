"""Node functions for the multi-agent conversation graph"""

from graph.state import UnifiedState
from agents.gmail_agent import get_gmail_agent, get_gmail_tools
from agents.calendar_agent import get_calendar_agent, get_calendar_tools
from agents.orchestrator_agent import get_orchestrator_agent
from tools.gmail_tools import GmailDeps
from tools.calendar_tools import CalendarDeps
from utils.logging import get_logger

logger = get_logger()


async def user_input_node(state: UnifiedState) -> dict:
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


async def gmail_agent_node(state: UnifiedState) -> dict:
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


def should_continue(state: UnifiedState) -> str:
    """Determine if conversation should continue"""
    if state.get("continue_conversation", True):
        return "continue"
    return "end"


async def orchestrator_node(state: UnifiedState) -> dict:
    """Orchestrator node that uses LLM to classify user intent and route to appropriate agent(s)"""
    user_query = state["user_query"]

    logger.debug(f"ORCHESTRATOR_NODE - Classifying intent for: {user_query}")

    try:
        # Get orchestrator agent
        orchestrator = get_orchestrator_agent()

        # Run orchestrator to classify intent
        result = await orchestrator.run(user_query)

        # Parse the JSON response from the agent
        # AgentRunResult has .output attribute, not .data
        response_text = str(result.output)
        logger.debug(f"ORCHESTRATOR - Raw response: {response_text}")

        # Try to parse JSON from the response
        import json
        try:
            # Try to extract JSON from the response
            if "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]
                parsed = json.loads(json_str)
                agent_type = parsed.get("agent_type", "gmail")
                reasoning = parsed.get("reasoning", "No reasoning provided")
            else:
                # Fallback if no JSON found
                raise ValueError("No JSON found in response")
        except (json.JSONDecodeError, ValueError) as parse_error:
            logger.warning(f"Failed to parse orchestrator response: {parse_error}")
            # Default to gmail if parsing fails
            agent_type = "gmail"
            reasoning = "Failed to parse orchestrator response, defaulting to Gmail"

        logger.info(f"ORCHESTRATOR - Routing to: {agent_type.upper()}")
        logger.info(f"ORCHESTRATOR - Reasoning: {reasoning}")

        print(f"\n[Orchestrator] Routing to: {agent_type}")
        print(f"[Orchestrator] Reasoning: {reasoning}\n")

        return {
            "agent_type": agent_type
        }

    except Exception as e:
        error_msg = f"Error in orchestrator: {str(e)}"
        logger.error(error_msg)
        # Default to gmail on error
        return {
            "agent_type": "gmail"
        }


def route_to_agent(state: UnifiedState) -> str:
    """Router function that determines which agent node to route to based on orchestrator decision"""
    agent_type = state.get("agent_type", "gmail")

    logger.debug(f"ROUTER - Agent type: {agent_type}")

    if agent_type == "calendar":
        return "calendar_agent"
    elif agent_type == "both":
        # For "both", we'll route to gmail first, then calendar
        # This will be handled by the graph structure
        return "gmail_agent"
    else:
        return "gmail_agent"


async def calendar_agent_node(state: UnifiedState) -> dict:
    """Run the Calendar agent - similar to gmail_agent_node"""
    user_query = state["user_query"]

    logger.debug(f"CALENDAR_AGENT_NODE - Current state keys: {list(state.keys())}")
    logger.debug(f"CALENDAR_AGENT_NODE - User query: {user_query}")
    logger.debug(f"CALENDAR_AGENT_NODE - Existing messages: {state.get('messages', [])}")

    # Check conversation history for context
    existing_messages = state.get("messages", [])
    if existing_messages:
        logger.info(f"Calendar agent has {len(existing_messages)} messages in memory for context")
    else:
        logger.info("No conversation history available - calendar agent starting fresh")

    print(f"\n[Calendar Agent] Processing: {user_query}")

    try:
        # Get Calendar tools instance
        calendar_tools = get_calendar_tools()

        # Create dependencies with event context and Calendar service
        deps = CalendarDeps(
            events=state.get('events', []),
            calendar_service=calendar_tools
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

        agent = get_calendar_agent()

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
        logger.info(f"Calendar agent response: {response}")
        logger.debug(f"Tool calls made: {tool_calls}")

        # Display the response
        print(f"\n[Calendar Agent] Answer: {response}\n")

        # Update events in state from deps (deps are modified in place)
        events_update = {}
        if deps.events:
            events_update['events'] = deps.events

        return {
            "agent_response": response,
            "messages": [{"role": "assistant", "content": str(response)}],
            "continue_conversation": not end_conversation_called,
            **events_update
        }

    except Exception as e:
        error_msg = f"Error processing Calendar query: {str(e)}"
        logger.error(error_msg)
        return {
            "agent_response": error_msg,
            "messages": [{"role": "assistant", "content": error_msg}],
            "continue_conversation": True
        }

