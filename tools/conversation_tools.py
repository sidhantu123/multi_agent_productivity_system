"""Conversation control tools for the weather agent"""

from pydantic_ai import RunContext
from tools.location_tools import WeatherDeps


async def end_conversation(ctx: RunContext[WeatherDeps]) -> str:
    """End the conversation with the user.

    Use this tool when the user wants to exit, quit, stop, or end the conversation.
    Examples: "goodbye", "quit", "exit", "turn off application", "stop", "bye"

    Returns:
        Confirmation message
    """
    return "Conversation ended. Goodbye!"
