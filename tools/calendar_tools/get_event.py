"""Get specific calendar event details tool"""

from typing import Optional, Dict, Any
from pydantic_ai import RunContext
from .core import CalendarDeps


def get_event_details(ctx: RunContext[CalendarDeps], event_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific calendar event
    
    Args:
        event_id: The Google Calendar event ID
    
    Returns:
        Event details including title, time, attendees, location, description
    """
    event = ctx.deps.calendar_service.get_event(event_id)
    return event

