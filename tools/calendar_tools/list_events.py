"""List upcoming calendar events tool"""

from typing import List, Dict, Any
from pydantic_ai import RunContext
from .core import CalendarDeps


def list_upcoming_events(ctx: RunContext[CalendarDeps], max_results: int = 10, days_ahead: int = 7) -> List[Dict[str, Any]]:
    """
    List upcoming calendar events
    
    Args:
        max_results: Maximum number of events to return (default 10)
        days_ahead: How many days ahead to look (default 7)
    
    Returns:
        List of upcoming events with details (title, time, attendees, location)
    """
    events = ctx.deps.calendar_service.list_upcoming_events(
        max_results=max_results,
        days_ahead=days_ahead
    )
    
    # Update context
    ctx.deps.events = events
    
    return events

