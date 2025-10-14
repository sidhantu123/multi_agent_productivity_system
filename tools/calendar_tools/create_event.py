"""Create calendar event tool"""

from typing import Optional, List, Dict, Any
from pydantic_ai import RunContext
from .core import CalendarDeps


def schedule_meeting(
    ctx: RunContext[CalendarDeps],
    title: str,
    start_time: str,
    end_time: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Schedule a new calendar meeting/event
    
    Args:
        title: Meeting title/subject
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS, e.g., '2024-03-20T14:00:00')
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS, e.g., '2024-03-20T15:00:00')
        description: Optional meeting description or agenda
        location: Optional meeting location (can be a physical location or video call link)
        attendees: Optional list of attendee email addresses
    
    Returns:
        Created event details including event ID, link, and confirmation
    
    Example:
        schedule_meeting(
            title="Team Standup",
            start_time="2024-03-20T09:00:00",
            end_time="2024-03-20T09:30:00",
            attendees=["john@example.com", "sarah@example.com"]
        )
    """
    event = ctx.deps.calendar_service.create_event(
        summary=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        location=location,
        attendees=attendees
    )
    
    return event

