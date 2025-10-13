"""Conversation control tools"""

from typing import Any
from pydantic_ai import RunContext


async def end_conversation(ctx: RunContext[Any]) -> str:
    """End the conversation with the user.

    Use this tool when the user wants to exit, quit, stop, or end the conversation.
    Examples: "goodbye", "quit", "exit", "turn off application", "stop", "bye"

    Returns:
        Confirmation message
    """
    return "Conversation ended. Goodbye!"
