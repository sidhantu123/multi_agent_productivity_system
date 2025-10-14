"""Manage calendar event attendees tools"""

from typing import List, Optional, Dict, Any
from pydantic_ai import RunContext
from .core import CalendarDeps


def add_attendees_to_meeting(
    ctx: RunContext[CalendarDeps],
    event_id: str,
    attendee_emails: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Add attendees to an existing calendar meeting
    
    Args:
        event_id: The Google Calendar event ID
        attendee_emails: List of email addresses to add to the meeting
    
    Returns:
        Updated event details with new attendee list
    
    Example:
        add_attendees_to_meeting(
            event_id="abc123xyz",
            attendee_emails=["newperson@example.com", "another@example.com"]
        )
    """
    event = ctx.deps.calendar_service.add_attendees(
        event_id=event_id,
        attendee_emails=attendee_emails
    )
    
    return event


def remove_attendees_from_meeting(
    ctx: RunContext[CalendarDeps],
    event_id: str,
    attendee_emails: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Remove attendees from an existing calendar meeting
    
    Args:
        event_id: The Google Calendar event ID
        attendee_emails: List of email addresses to remove from the meeting
    
    Returns:
        Updated event details with updated attendee list
    
    Example:
        remove_attendees_from_meeting(
            event_id="abc123xyz",
            attendee_emails=["person@example.com"]
        )
    """
    event = ctx.deps.calendar_service.remove_attendees(
        event_id=event_id,
        attendee_emails=attendee_emails
    )
    
    return event

