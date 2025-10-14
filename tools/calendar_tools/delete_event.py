"""Delete calendar event tool"""

from pydantic_ai import RunContext
from .core import CalendarDeps


def delete_meeting(ctx: RunContext[CalendarDeps], event_id: str) -> bool:
    """
    Delete a calendar meeting/event
    
    Args:
        event_id: The Google Calendar event ID to delete
    
    Returns:
        True if the meeting was successfully deleted, False otherwise
    
    Example:
        delete_meeting(event_id="abc123xyz")
    """
    success = ctx.deps.calendar_service.delete_event(event_id)
    return success

