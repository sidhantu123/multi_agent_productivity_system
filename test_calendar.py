"""Simple CLI test for Google Calendar Agent with Pydantic AI built-in memory"""

import asyncio
from dotenv import load_dotenv
from agents.calendar_agent import get_calendar_agent, get_calendar_tools
from tools.calendar_tools import CalendarDeps


async def main():
    """Simple interactive CLI for testing the Calendar agent"""
    # Load environment variables
    load_dotenv()
    
    print("=" * 60)
    print("Google Calendar Agent - CLI Test with Pydantic AI Memory")
    print("=" * 60)
    print("\nInitializing Calendar agent...")
    
    # Get agent and calendar service
    agent = get_calendar_agent()
    calendar_service = get_calendar_tools()
    
    print("✓ Calendar agent ready!")
    print("\nYou can:")
    print("  - List upcoming events: 'show my upcoming meetings'")
    print("  - Schedule meetings: 'schedule a meeting tomorrow at 2pm'")
    print("  - Modify times: 'reschedule event X to 3pm'")
    print("  - Add attendees: 'add john@example.com to the meeting'")
    print("  - Delete events: 'delete the team standup meeting'")
    print("  - Type 'quit' or 'exit' to end")
    print("  - Type '/history' to view conversation history\n")
    
    # Pydantic AI built-in message history - starts as None for first message
    message_history = None
    
    # Chat loop
    conversation_active = True
    while conversation_active:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Check for special commands
            if user_input.lower() in ['/history', '/memory']:
                print("\n" + "=" * 60)
                print("CONVERSATION HISTORY (Pydantic AI)")
                print("=" * 60)
                if message_history:
                    for i, msg in enumerate(message_history, 1):
                        print(f"\n--- Message {i} ---")
                        print(f"Type: {type(msg).__name__}")
                        print(f"Content: {msg}")
                else:
                    print("No conversation history yet.")
                print("=" * 60 + "\n")
                continue
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("\nCalendar Agent: Goodbye! Have a great day!")
                break
            
            # Create dependencies for this turn
            deps = CalendarDeps(
                events=[],
                calendar_service=calendar_service
            )
            
            # Run the agent with Pydantic AI's built-in message history
            result = await agent.run(
                user_input,
                message_history=message_history,
                deps=deps
            )
            
            # Display tool calls that were made
            print()
            tool_calls_found = []
            for msg in result.new_messages():
                if hasattr(msg, 'parts'):
                    for part in msg.parts:
                        if hasattr(part, 'part_kind') and part.part_kind == 'tool-call':
                            tool_name = part.tool_name if hasattr(part, 'tool_name') else 'unknown'
                            tool_calls_found.append(tool_name)
            
            if tool_calls_found:
                print("🔧 Tool Calls:")
                for tool_name in tool_calls_found:
                    print(f"   → {tool_name}")
                print()
            
            # Display final response
            # Extract the text from the last assistant message
            response_text = None
            for msg in reversed(result.new_messages()):
                if hasattr(msg, 'parts'):
                    for part in msg.parts:
                        if hasattr(part, 'part_kind') and part.part_kind == 'text':
                            if hasattr(part, 'content'):
                                response_text = part.content
                                break
                if response_text:
                    break
            
            # Fallback to string representation
            if not response_text:
                response_text = str(result)
            
            print(f"Calendar Agent: {response_text}")
            print()
            
            # Use Pydantic AI's built-in message tracking
            message_history = result.all_messages()
            
        except KeyboardInterrupt:
            print("\n\nCalendar Agent: Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            print("Please try again.\n")


if __name__ == "__main__":
    asyncio.run(main())

