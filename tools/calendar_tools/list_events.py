"""List upcoming calendar events tool"""

from typing import List, Dict, Any, Optional
from pydantic_ai import RunContext
from .core import CalendarDeps


def list_upcoming_events(
    ctx: RunContext[CalendarDeps],
    max_results: int = 10,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List calendar events within a specified time range

    Args:
        max_results: Maximum number of events to return (default 10)
        start_time: Start of time range in ISO format (e.g., "2025-10-15T00:00:00Z").
                   If not provided, uses current time.
        end_time: End of time range in ISO format (e.g., "2025-10-15T23:59:59Z").
                 If not provided, looks 7 days ahead from start_time.

    Returns:
        List of events with details (title, time, attendees, location)

    Examples:
        - For "today": start_time="2025-10-15T00:00:00Z", end_time="2025-10-15T23:59:59Z"
        - For "this week": start_time="2025-10-15T00:00:00Z", end_time="2025-10-22T23:59:59Z"
        - For "next month": start_time="2025-11-01T00:00:00Z", end_time="2025-11-30T23:59:59Z"

    IMPORTANT: Always use get_current_datetime() tool first to get the correct current date/time,
    then calculate the appropriate start_time and end_time based on the user's query.
    """
    events = ctx.deps.calendar_service.list_events_in_range(
        max_results=max_results,
        start_time=start_time,
        end_time=end_time
    )

    # Update context
    ctx.deps.events = events

    return events

