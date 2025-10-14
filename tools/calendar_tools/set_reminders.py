"""Set event notification reminders tool"""

from typing import List, Optional, Dict, Any
from pydantic_ai import RunContext
from .core import CalendarDeps


def configure_event_notifications(
    ctx: RunContext[CalendarDeps],
    event_id: str,
    reminder_minutes: List[int]
) -> Optional[Dict[str, Any]]:
    """
    Configure notification reminders for a calendar event
    
    Args:
        event_id: The Google Calendar event ID
        reminder_minutes: List of times (in minutes) before the event to send notifications
                         Examples:
                         - [10] = 10 minutes before
                         - [10, 30] = 10 and 30 minutes before
                         - [5, 15, 60] = 5 min, 15 min, and 1 hour before
    
    Returns:
        Updated event details with new reminder settings
    
    Common reminder times:
    - 5 minutes = [5]
    - 10 minutes = [10]
    - 15 minutes = [15]
    - 30 minutes = [30]
    - 1 hour = [60]
    - 1 day = [1440]
    - Multiple: [10, 30] for both 10 and 30 minute reminders
    
    Examples:
        # Set 10 and 30 minute reminders
        configure_event_notifications(
            event_id="abc123",
            reminder_minutes=[10, 30]
        )
        
        # Set single 1-hour reminder
        configure_event_notifications(
            event_id="abc123",
            reminder_minutes=[60]
        )
    
    Note: This replaces any existing reminders on the event.
    """
    event = ctx.deps.calendar_service.set_event_reminders(
        event_id=event_id,
        reminders=reminder_minutes
    )
    
    return event

