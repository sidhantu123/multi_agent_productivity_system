"""Get current date and time tool"""

from datetime import datetime
from typing import Dict, Any
from pydantic_ai import RunContext
from .core import CalendarDeps


def get_current_datetime(ctx: RunContext[CalendarDeps]) -> Dict[str, Any]:
    """
    Get the current date and time
    
    Returns:
        Current date, time, day of week, and ISO formatted timestamp
    
    Use this tool whenever you need to know:
    - Today's date
    - Current time
    - Day of the week
    - Calculate dates like "tomorrow", "next week", "in 3 days"
    """
    now = datetime.now()
    
    return {
        'datetime': now.isoformat(),
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M:%S'),
        'day_of_week': now.strftime('%A'),
        'formatted': now.strftime('%A, %B %d, %Y at %I:%M %p'),
        'year': now.year,
        'month': now.month,
        'day': now.day,
        'hour': now.hour,
        'minute': now.minute
    }

