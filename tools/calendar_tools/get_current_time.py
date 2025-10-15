"""Get current date and time tool"""

from datetime import datetime, timedelta
from typing import Dict, Any
from pydantic_ai import RunContext
from .core import CalendarDeps


def get_current_datetime(ctx: RunContext[CalendarDeps]) -> Dict[str, Any]:
    """
    Get the current date and time in PST/PDT timezone

    Returns:
        Current date, time, day of week, and ISO formatted timestamp
        Also includes tomorrow's date for convenience

    Use this tool whenever you need to know:
    - Today's date
    - Current time
    - Day of the week
    - Calculate dates like "tomorrow", "next week", "in 3 days"

    IMPORTANT: The times returned are in PST/PDT (UTC-8 or UTC-7)
    For Google Calendar API, you MUST convert to UTC:
    - PST (winter): Add 8 hours to convert to UTC
    - PDT (summer): Add 7 hours to convert to UTC

    Example: "3 PM PST tomorrow" where tomorrow is 2025-10-16:
    - Tomorrow's date: 2025-10-16
    - Start time in PST: 2025-10-16T15:00:00 (3 PM)
    - Start time in UTC: 2025-10-16T23:00:00 (3 PM + 8 hours = 11 PM UTC)
    - End time in PST: 2025-10-16T16:00:00 (4 PM)
    - End time in UTC: 2025-10-17T00:00:00 (4 PM + 8 hours = midnight next day UTC)
    """
    now = datetime.now()
    tomorrow = now + timedelta(days=1)

    return {
        'datetime': now.isoformat(),
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M:%S'),
        'day_of_week': now.strftime('%A'),
        'formatted': now.strftime('%A, %B %d, %Y at %I:%M %p PST'),
        'year': now.year,
        'month': now.month,
        'day': now.day,
        'hour': now.hour,
        'minute': now.minute,
        'tomorrow_date': tomorrow.strftime('%Y-%m-%d'),
        'tomorrow_day': tomorrow.strftime('%A'),
        'timezone_note': 'Times are in PST/PDT. For Google Calendar API, convert to UTC by adding 8 hours (PST) or 7 hours (PDT)',
        'utc_offset_hours': 8  # Assume PST for now (you can make this dynamic based on DST if needed)
    }

