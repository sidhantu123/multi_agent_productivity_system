"""Update calendar event tool"""

from typing import Optional, Dict, Any
from pydantic_ai import RunContext
from .core import CalendarDeps


def modify_meeting_time(
    ctx: RunContext[CalendarDeps],
    event_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Modify the time of an existing calendar meeting
    
    Args:
        event_id: The Google Calendar event ID
        start_time: New start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        end_time: New end time in ISO format (YYYY-MM-DDTHH:MM:SS)
    
    Returns:
        Updated event details
    
    Example:
        modify_meeting_time(
            event_id="abc123xyz",
            start_time="2024-03-20T10:00:00",
            end_time="2024-03-20T11:00:00"
        )
    """
    event = ctx.deps.calendar_service.update_event(
        event_id=event_id,
        start_time=start_time,
        end_time=end_time
    )
    
    return event


def update_meeting_details(
    ctx: RunContext[CalendarDeps],
    event_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Update details of an existing calendar meeting
    
    Args:
        event_id: The Google Calendar event ID
        title: New meeting title
        description: New meeting description
        location: New meeting location
    
    Returns:
        Updated event details
    """
    event = ctx.deps.calendar_service.update_event(
        event_id=event_id,
        summary=title,
        description=description,
        location=location
    )
    
    return event

