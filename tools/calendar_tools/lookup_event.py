"""Helper tool to lookup events by number or title"""

from typing import Optional, Dict, Any
from pydantic_ai import RunContext
from .core import CalendarDeps


def lookup_event_by_reference(
    ctx: RunContext[CalendarDeps],
    reference: str
) -> str:
    """
    Look up an event ID by reference (number or title).

    Use this tool when the user refers to "the first event", "event 2", "the second calendar event", etc.
    This will return the actual event ID that you should use with other calendar tools.

    Args:
        reference: Event reference like "1", "2", "first", "second", "third", or event title

    Returns:
        Event ID string to use with other calendar tools, or error message if not found
    """
    if not ctx.deps.events:
        return "No events in context. Please list events first using list_upcoming_events."

    # Parse numeric references
    number_words = {
        "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
        "1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "5th": 5
    }

    # Try to parse as number
    event_number = None
    ref_lower = reference.lower().strip()

    if ref_lower in number_words:
        event_number = number_words[ref_lower]
    elif ref_lower.isdigit():
        event_number = int(ref_lower)
    else:
        # Try word extraction
        for word, num in number_words.items():
            if word in ref_lower:
                event_number = num
                break

    # Look up by number
    if event_number is not None:
        if 1 <= event_number <= len(ctx.deps.events):
            event = ctx.deps.events[event_number - 1]  # Convert to 0-indexed
            event_id = event.get('id')
            event_title = event.get('summary', 'Untitled')
            return f"Event ID: {event_id} (Event #{event_number}: {event_title})"
        else:
            return f"Event number {event_number} not found. Only {len(ctx.deps.events)} events in context."

    # Look up by title (partial match)
    ref_lower = reference.lower()
    for idx, event in enumerate(ctx.deps.events):
        event_title = event.get('summary', '').lower()
        if ref_lower in event_title or event_title in ref_lower:
            event_id = event.get('id')
            return f"Event ID: {event_id} (Event #{idx+1}: {event.get('summary')})"

    available_events = ', '.join([f"#{i+1}: {e.get('summary')}" for i, e in enumerate(ctx.deps.events)])
    return f"Could not find event matching '{reference}'. Available events: {available_events}"
