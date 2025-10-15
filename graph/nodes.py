"""Node functions for the multi-agent conversation graph"""

from typing import Literal
from langgraph.types import Command
from langgraph.graph import END

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


async def gmail_agent_node(state: UnifiedState) -> Command[Literal["calendar_agent", "user_input", END]]:
    """Run the Gmail agent - LangGraph handles memory automatically"""
    user_query = state["user_query"]
    agent_type = state.get("agent_type", "gmail")

    # Use specialized instruction if available (for multi-agent tasks)
    gmail_instruction = state.get("gmail_instruction", user_query)

    # Log state for debugging
    logger.debug(f"GMAIL_AGENT_NODE - Current state keys: {list(state.keys())}")
    logger.debug(f"GMAIL_AGENT_NODE - User query: {user_query}")
    logger.debug(f"GMAIL_AGENT_NODE - Gmail instruction: {gmail_instruction}")
    logger.debug(f"GMAIL_AGENT_NODE - Agent type: {agent_type}")
    logger.debug(f"GMAIL_AGENT_NODE - Existing messages: {state.get('messages', [])}")

    # Check conversation history for context
    existing_messages = state.get("messages", [])
    if existing_messages:
        logger.info(f"Agent has {len(existing_messages)} messages in memory for context")
    else:
        logger.info("No conversation history available - agent starting fresh")

    print(f"\n[Gmail Agent] Processing: {gmail_instruction}")

    try:
        # Get Gmail tools instance
        gmail_tools = get_gmail_tools()

        # Create dependencies with email context and Gmail service
        deps = GmailDeps(
            emails=state.get('emails', []),
            gmail_service=gmail_tools
        )

        # Build conversation context using specialized instruction
        conversation_context = gmail_instruction
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
                conversation_context = "Previous conversation:\n" + "\n".join(context_parts) + "\n\nCurrent question: " + gmail_instruction

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
        logger.info(f"Gmail agent response: {response}")
        logger.debug(f"Tool calls made: {tool_calls}")

        # Display the response
        print(f"\n[Gmail Agent] Answer: {response}\n")

        # Update emails in state from deps (deps are modified in place)
        emails_update = {}
        if deps.emails:
            emails_update['emails'] = deps.emails

        # Determine where to route next using Command
        execution_order = state.get("execution_order", "gmail_first")

        if agent_type == "both" and execution_order == "gmail_first":
            # If we ran gmail first, now route to calendar
            logger.info("GMAIL_AGENT - Routing to calendar_agent (gmail_first order)")
            return Command(
                goto="calendar_agent",
                update={
                    "agent_response": response,
                    "messages": [{"role": "assistant", "content": str(response)}],
                    "continue_conversation": not end_conversation_called,
                    **emails_update
                }
            )
        elif end_conversation_called:
            # End conversation if requested
            logger.info("GMAIL_AGENT - Ending conversation")
            return Command(
                goto=END,
                update={
                    "agent_response": response,
                    "messages": [{"role": "assistant", "content": str(response)}],
                    "continue_conversation": False,
                    **emails_update
                }
            )
        else:
            # Route back to user_input (for single agent or after calendar_first)
            logger.info("GMAIL_AGENT - Routing back to user_input")
            return Command(
                goto="user_input",
                update={
                    "agent_response": response,
                    "messages": [{"role": "assistant", "content": str(response)}],
                    "continue_conversation": True,
                    **emails_update
                }
            )

    except Exception as e:
        error_msg = f"Error processing Gmail query: {str(e)}"
        logger.error(error_msg)
        return Command(
            goto="user_input",
            update={
                "agent_response": error_msg,
                "messages": [{"role": "assistant", "content": error_msg}],
                "continue_conversation": True
            }
        )


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
                execution_order = parsed.get("execution_order", "gmail_first")
                gmail_instruction = parsed.get("gmail_instruction", user_query)
                calendar_instruction = parsed.get("calendar_instruction", user_query)
            else:
                # Fallback if no JSON found
                raise ValueError("No JSON found in response")
        except (json.JSONDecodeError, ValueError) as parse_error:
            logger.warning(f"Failed to parse orchestrator response: {parse_error}")
            # Default to gmail if parsing fails
            agent_type = "gmail"
            reasoning = "Failed to parse orchestrator response, defaulting to Gmail"
            execution_order = "gmail_first"
            gmail_instruction = user_query
            calendar_instruction = user_query

        logger.info(f"ORCHESTRATOR - Routing to: {agent_type.upper()}")
        logger.info(f"ORCHESTRATOR - Reasoning: {reasoning}")

        print(f"\n[Orchestrator] Routing to: {agent_type}")
        print(f"[Orchestrator] Reasoning: {reasoning}")

        # Handle termination request
        if agent_type == "terminate":
            print("\nGoodbye! Terminating the application.\n")
            return {
                "agent_type": agent_type,
                "continue_conversation": False,
                "execution_order": execution_order,
                "gmail_instruction": gmail_instruction,
                "calendar_instruction": calendar_instruction
            }

        if agent_type == "both":
            print(f"[Orchestrator] Execution order: {execution_order}")
            print(f"[Orchestrator] Gmail instruction: {gmail_instruction}")
            print(f"[Orchestrator] Calendar instruction: {calendar_instruction}")
        print()

        return {
            "agent_type": agent_type,
            "execution_order": execution_order,
            "gmail_instruction": gmail_instruction,
            "calendar_instruction": calendar_instruction
        }

    except Exception as e:
        error_msg = f"Error in orchestrator: {str(e)}"
        logger.error(error_msg)
        # Default to gmail on error
        return {
            "agent_type": "gmail",
            "execution_order": "gmail_first",
            "gmail_instruction": user_query,
            "calendar_instruction": user_query
        }


def route_to_agent(state: UnifiedState) -> str:
    """Router function that determines which agent node to route to based on orchestrator decision"""
    agent_type = state.get("agent_type", "gmail")
    execution_order = state.get("execution_order", "gmail_first")

    logger.debug(f"ROUTER - Agent type: {agent_type}, Execution order: {execution_order}")

    if agent_type == "terminate":
        # Terminate - should not reach here as orchestrator sets continue_conversation=False
        logger.info("ROUTER - Termination requested")
        return "END"
    elif agent_type == "calendar":
        return "calendar_agent"
    elif agent_type == "both":
        # For "both", route based on execution_order
        if execution_order == "calendar_first":
            logger.info("ROUTER - Routing to calendar_agent first (calendar_first order)")
            return "calendar_agent"
        else:
            logger.info("ROUTER - Routing to gmail_agent first (gmail_first order)")
            return "gmail_agent"
    else:
        return "gmail_agent"


async def calendar_agent_node(state: UnifiedState) -> Command[Literal["user_input", END]]:
    """Run the Calendar agent - similar to gmail_agent_node"""
    user_query = state["user_query"]

    # Use specialized instruction if available (for multi-agent tasks)
    calendar_instruction = state.get("calendar_instruction", user_query)

    logger.debug(f"CALENDAR_AGENT_NODE - Current state keys: {list(state.keys())}")
    logger.debug(f"CALENDAR_AGENT_NODE - User query: {user_query}")
    logger.debug(f"CALENDAR_AGENT_NODE - Calendar instruction: {calendar_instruction}")
    logger.debug(f"CALENDAR_AGENT_NODE - Existing messages: {state.get('messages', [])}")

    # Check conversation history for context
    existing_messages = state.get("messages", [])
    if existing_messages:
        logger.info(f"Calendar agent has {len(existing_messages)} messages in memory for context")
    else:
        logger.info("No conversation history available - calendar agent starting fresh")

    print(f"\n[Calendar Agent] Processing: {calendar_instruction}")

    try:
        # Get Calendar tools instance
        calendar_tools = get_calendar_tools()

        # Create dependencies with event context and Calendar service
        deps = CalendarDeps(
            events=state.get('events', []),
            calendar_service=calendar_tools
        )

        # Build conversation context using specialized instruction
        conversation_context = calendar_instruction
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
                conversation_context = "Previous conversation:\n" + "\n".join(context_parts) + "\n\nCurrent question: " + calendar_instruction

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

        # Calendar agent routes based on agent_type and execution_order
        agent_type = state.get("agent_type", "calendar")
        execution_order = state.get("execution_order", "gmail_first")

        if agent_type == "both" and execution_order == "calendar_first":
            # If we ran calendar first, now route to gmail
            logger.info("CALENDAR_AGENT - Routing to gmail_agent (calendar_first order)")
            return Command(
                goto="gmail_agent",
                update={
                    "agent_response": response,
                    "messages": [{"role": "assistant", "content": str(response)}],
                    "continue_conversation": not end_conversation_called,
                    **events_update
                }
            )
        elif end_conversation_called:
            logger.info("CALENDAR_AGENT - Ending conversation")
            return Command(
                goto=END,
                update={
                    "agent_response": response,
                    "messages": [{"role": "assistant", "content": str(response)}],
                    "continue_conversation": False,
                    **events_update
                }
            )
        else:
            logger.info("CALENDAR_AGENT - Routing back to user_input")
            return Command(
                goto="user_input",
                update={
                    "agent_response": response,
                    "messages": [{"role": "assistant", "content": str(response)}],
                    "continue_conversation": True,
                    **events_update
                }
            )

    except Exception as e:
        error_msg = f"Error processing Calendar query: {str(e)}"
        logger.error(error_msg)
        return Command(
            goto="user_input",
            update={
                "agent_response": error_msg,
                "messages": [{"role": "assistant", "content": error_msg}],
                "continue_conversation": True
            }
        )

