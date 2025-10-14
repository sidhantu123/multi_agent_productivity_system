"""Add Google Meet to calendar events tools"""

from typing import Optional, List, Dict, Any
from pydantic_ai import RunContext
from .core import CalendarDeps


def add_google_meet_to_event(
    ctx: RunContext[CalendarDeps],
    event_id: str
) -> Optional[Dict[str, Any]]:
    """
    Add a Google Meet video conference link to an existing calendar event
    
    Args:
        event_id: The Google Calendar event ID
    
    Returns:
        Updated event details with Google Meet link included
    
    Example:
        add_google_meet_to_event(event_id="abc123xyz")
    
    The Google Meet link will be automatically generated and:
    - Added to the event
    - Sent to all attendees
    - Available for joining the meeting
    """
    event = ctx.deps.calendar_service.add_google_meet(event_id)
    return event


def schedule_meeting_with_google_meet(
    ctx: RunContext[CalendarDeps],
    title: str,
    start_time: str,
    end_time: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Schedule a new calendar meeting with Google Meet video conference included
    
    Args:
        title: Meeting title/subject
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS)
        description: Optional meeting description or agenda
        location: Optional meeting location
        attendees: Optional list of attendee email addresses
    
    Returns:
        Created event details including Google Meet link
    
    Example:
        schedule_meeting_with_google_meet(
            title="Team Standup",
            start_time="2024-03-20T09:00:00",
            end_time="2024-03-20T09:30:00",
            attendees=["john@example.com", "sarah@example.com"]
        )
    
    This automatically creates a Google Meet link that all attendees can use to join.
    """
    event = ctx.deps.calendar_service.create_event_with_meet(
        summary=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        location=location,
        attendees=attendees
    )
    
    return event

