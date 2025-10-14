"""Google Calendar tools package"""

from .core import CalendarTools, CalendarDeps, SCOPES
from .list_events import list_upcoming_events
from .get_event import get_event_details
from .create_event import schedule_meeting
from .update_event import modify_meeting_time, update_meeting_details
from .manage_attendees import add_attendees_to_meeting, remove_attendees_from_meeting
from .delete_event import delete_meeting
from .update_rsvp import update_rsvp_status
from .get_current_time import get_current_datetime
from .add_google_meet import add_google_meet_to_event, schedule_meeting_with_google_meet
from .set_reminders import configure_event_notifications


__all__ = [
    # Core
    'CalendarTools',
    'CalendarDeps',
    'SCOPES',
    
    # Utility tools
    'get_current_datetime',
    
    # Viewing tools
    'list_upcoming_events',
    'get_event_details',
    
    # Creation tools
    'schedule_meeting',
    'schedule_meeting_with_google_meet',
    
    # Modification tools
    'modify_meeting_time',
    'update_meeting_details',
    'add_attendees_to_meeting',
    'remove_attendees_from_meeting',
    'update_rsvp_status',
    'add_google_meet_to_event',
    'configure_event_notifications',
    
    # Deletion tools
    'delete_meeting',
]

