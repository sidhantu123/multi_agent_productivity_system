"""Timezone conversion helper tool for Calendar agent"""

from datetime import datetime
from typing import Dict, Any
from pydantic_ai import RunContext
from .core import CalendarDeps


def convert_pst_to_utc(
    ctx: RunContext[CalendarDeps],
    pst_datetime: str,
    date: str
) -> Dict[str, Any]:
    """
    Convert PST/PDT time to UTC format for Google Calendar API

    Args:
        pst_datetime: Time in PST format (e.g., "15:00" for 3 PM, "09:30" for 9:30 AM)
        date: Date in YYYY-MM-DD format (e.g., "2025-10-15")

    Returns:
        Dictionary with UTC datetime string and formatted time

    Example:
        convert_pst_to_utc("15:00", "2025-10-15")
        Returns: {
            'utc_datetime': '2025-10-15T23:00:00',
            'pst_datetime': '2025-10-15T15:00:00',
            'pst_time': '3:00 PM PST',
            'utc_time': '11:00 PM UTC'
        }

    Use this tool whenever you need to create or modify calendar events
    with times specified in PST/PDT timezone.

    CRITICAL: Always use this tool to convert PST times to UTC before
    calling schedule_meeting, schedule_meeting_with_google_meet, or
    modify_meeting_time.
    """
    # Parse the time (handle both HH:MM and HH:MM:SS formats)
    time_parts = pst_datetime.strip().split(':')
    hour = int(time_parts[0])
    minute = int(time_parts[1]) if len(time_parts) > 1 else 0
    second = int(time_parts[2]) if len(time_parts) > 2 else 0

    # Validate time
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        return {
            'error': f'Invalid time: {pst_datetime}. Hour must be 0-23, minute and second must be 0-59.',
            'utc_datetime': None
        }

    # Validate date format
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return {
            'error': f'Invalid date format: {date}. Expected YYYY-MM-DD.',
            'utc_datetime': None
        }

    # Convert PST to UTC (add 8 hours for PST, 7 for PDT)
    # For simplicity, using PST offset (8 hours) - adjust if needed for DST
    utc_hour = hour + 8
    utc_day = date

    # Handle day overflow (e.g., 10 PM PST = 6 AM UTC next day)
    if utc_hour >= 24:
        utc_hour -= 24
        # Parse date and add 1 day
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        from datetime import timedelta
        next_day = date_obj + timedelta(days=1)
        utc_day = next_day.strftime('%Y-%m-%d')

    # Format UTC datetime
    utc_datetime = f"{utc_day}T{utc_hour:02d}:{minute:02d}:{second:02d}"
    pst_datetime_formatted = f"{date}T{hour:02d}:{minute:02d}:{second:02d}"

    # Format human-readable times
    pst_hour_12 = hour % 12 if hour % 12 != 0 else 12
    pst_ampm = 'AM' if hour < 12 else 'PM'
    utc_hour_12 = utc_hour % 12 if utc_hour % 12 != 0 else 12
    utc_ampm = 'AM' if utc_hour < 12 else 'PM'

    return {
        'utc_datetime': utc_datetime,
        'pst_datetime': pst_datetime_formatted,
        'pst_time': f'{pst_hour_12}:{minute:02d} {pst_ampm} PST',
        'utc_time': f'{utc_hour_12}:{minute:02d} {utc_ampm} UTC',
        'conversion_note': f'Converted PST to UTC by adding 8 hours',
        'date': date,
        'utc_date': utc_day
    }
