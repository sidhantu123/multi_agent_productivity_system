"""Update RSVP status for calendar events tool"""

from typing import Optional, Dict, Any
from pydantic_ai import RunContext
from .core import CalendarDeps


def update_rsvp_status(
    ctx: RunContext[CalendarDeps],
    event_id: str,
    status: str,
    attendee_email: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Update your RSVP status for a calendar event
    
    Args:
        event_id: The Google Calendar event ID
        status: Your response status. Must be one of:
            - 'accepted' or 'going' - You will attend
            - 'declined' or 'not going' - You will not attend  
            - 'tentative' or 'maybe' - You might attend
            - 'needsAction' - No response yet
        attendee_email: Email of the attendee to update (defaults to your email)
    
    Returns:
        Updated event details with new RSVP status
    
    Examples:
        # Mark yourself as going
        update_rsvp_status(event_id="abc123", status="accepted")
        
        # Mark yourself as maybe
        update_rsvp_status(event_id="abc123", status="tentative")
        
        # Decline an event
        update_rsvp_status(event_id="abc123", status="declined")
    """
    # Normalize status to API values
    status_mapping = {
        'going': 'accepted',
        'accepted': 'accepted',
        'not going': 'declined',
        'declined': 'declined',
        'maybe': 'tentative',
        'tentative': 'tentative',
        'needsAction': 'needsAction',
        'no response': 'needsAction'
    }
    
    normalized_status = status_mapping.get(status.lower(), status)
    
    event = ctx.deps.calendar_service.update_rsvp_status(
        event_id=event_id,
        response_status=normalized_status,
        attendee_email=attendee_email
    )
    
    return event

