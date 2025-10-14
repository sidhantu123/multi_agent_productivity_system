"""Core Google Calendar API service layer - CalendarTools class and dependencies"""

import os
import pickle
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Google Calendar API scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar',  # Full calendar access
]


@dataclass
class CalendarDeps:
    """Dependencies for Calendar tools - holds calendar context"""
    events: List[dict]
    calendar_service: 'CalendarTools'


class CalendarTools:
    """Google Calendar API client for managing calendar events"""

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None
    ):
        self.credentials_path = credentials_path or os.getenv(
            'GOOGLE_CREDENTIALS_PATH',
            'config/google_credentials.json'
        )
        self.token_path = token_path or os.getenv(
            'GOOGLE_CALENDAR_TOKEN_PATH',
            'config/google_calendar_token.json'
        )
        self.service = None
        self.authenticate()

    def authenticate(self) -> None:
        """Authenticate with Google Calendar API"""
        creds = None

        # Load existing token
        if Path(self.token_path).exists():
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not Path(self.credentials_path).exists():
                    raise FileNotFoundError(
                        f"Google credentials not found at {self.credentials_path}. "
                        "Please ensure google_credentials.json is in the config folder."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials
            Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('calendar', 'v3', credentials=creds)

    def list_upcoming_events(
        self,
        max_results: int = 10,
        days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """
        List upcoming calendar events

        Args:
            max_results: Maximum number of events to return (default 10)
            days_ahead: How many days ahead to look (default 7)

        Returns:
            List of event dictionaries
        """
        if not self.service:
            raise RuntimeError("Calendar service not authenticated")

        try:
            # Get time range
            now = datetime.utcnow().isoformat() + 'Z'
            time_max = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            
            # Parse events into readable format
            parsed_events = []
            for event in events:
                parsed_event = self._parse_event(event)
                if parsed_event:
                    parsed_events.append(parsed_event)

            return parsed_events

        except HttpError as error:
            print(f"Error fetching calendar events: {error}")
            return []

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific calendar event

        Args:
            event_id: Google Calendar event ID

        Returns:
            Dictionary with event details
        """
        if not self.service:
            raise RuntimeError("Calendar service not authenticated")

        try:
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            return self._parse_event(event)

        except HttpError as error:
            print(f"Error fetching event {event_id}: {error}")
            return None

    def _parse_event(self, event: dict) -> Optional[Dict[str, Any]]:
        """Parse a Google Calendar event into a readable format"""
        try:
            # Get event times
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Parse attendees
            attendees = []
            if 'attendees' in event:
                attendees = [
                    {
                        'email': attendee.get('email'),
                        'name': attendee.get('displayName', attendee.get('email')),
                        'response_status': attendee.get('responseStatus', 'needsAction')
                    }
                    for attendee in event['attendees']
                ]

            # Check for Google Meet conference data
            meet_link = None
            if 'conferenceData' in event:
                entry_points = event['conferenceData'].get('entryPoints', [])
                for entry in entry_points:
                    if entry.get('entryPointType') == 'video':
                        meet_link = entry.get('uri')
                        break

            return {
                'id': event['id'],
                'summary': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'start_time': start,
                'end_time': end,
                'location': event.get('location', ''),
                'attendees': attendees,
                'organizer': event.get('organizer', {}).get('email'),
                'status': event.get('status', 'confirmed'),
                'html_link': event.get('htmlLink', ''),
                'meet_link': meet_link
            }
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None

    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new calendar event

        Args:
            summary: Event title
            start_time: Start time (ISO format: YYYY-MM-DDTHH:MM:SS)
            end_time: End time (ISO format: YYYY-MM-DDTHH:MM:SS)
            description: Event description
            location: Event location
            attendees: List of attendee email addresses

        Returns:
            Created event details or None if failed
        """
        if not self.service:
            raise RuntimeError("Calendar service not authenticated")

        try:
            event_body = {
                'summary': summary,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC',
                },
            }

            if description:
                event_body['description'] = description
            
            if location:
                event_body['location'] = location
            
            if attendees:
                event_body['attendees'] = [{'email': email} for email in attendees]

            event = self.service.events().insert(
                calendarId='primary',
                body=event_body,
                sendUpdates='all'  # Send email notifications to attendees
            ).execute()

            return self._parse_event(event)

        except HttpError as error:
            print(f"Error creating event: {error}")
            return None

    def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing calendar event

        Args:
            event_id: Google Calendar event ID
            summary: New event title
            start_time: New start time (ISO format)
            end_time: New end time (ISO format)
            description: New description
            location: New location

        Returns:
            Updated event details or None if failed
        """
        if not self.service:
            raise RuntimeError("Calendar service not authenticated")

        try:
            # Get existing event
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            # Update fields if provided
            if summary:
                event['summary'] = summary
            if start_time:
                event['start'] = {'dateTime': start_time, 'timeZone': 'UTC'}
            if end_time:
                event['end'] = {'dateTime': end_time, 'timeZone': 'UTC'}
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location

            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()

            return self._parse_event(updated_event)

        except HttpError as error:
            print(f"Error updating event: {error}")
            return None

    def add_attendees(
        self,
        event_id: str,
        attendee_emails: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Add attendees to an existing event

        Args:
            event_id: Google Calendar event ID
            attendee_emails: List of email addresses to add

        Returns:
            Updated event details or None if failed
        """
        if not self.service:
            raise RuntimeError("Calendar service not authenticated")

        try:
            # Get existing event
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            # Get existing attendees
            existing_attendees = event.get('attendees', [])
            existing_emails = {a['email'] for a in existing_attendees}

            # Add new attendees (avoid duplicates)
            for email in attendee_emails:
                if email not in existing_emails:
                    existing_attendees.append({'email': email})

            event['attendees'] = existing_attendees

            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()

            return self._parse_event(updated_event)

        except HttpError as error:
            print(f"Error adding attendees: {error}")
            return None

    def remove_attendees(
        self,
        event_id: str,
        attendee_emails: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Remove attendees from an existing event

        Args:
            event_id: Google Calendar event ID
            attendee_emails: List of email addresses to remove

        Returns:
            Updated event details or None if failed
        """
        if not self.service:
            raise RuntimeError("Calendar service not authenticated")

        try:
            # Get existing event
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            # Remove specified attendees
            existing_attendees = event.get('attendees', [])
            emails_to_remove = set(attendee_emails)
            
            updated_attendees = [
                a for a in existing_attendees 
                if a['email'] not in emails_to_remove
            ]

            event['attendees'] = updated_attendees

            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()

            return self._parse_event(updated_event)

        except HttpError as error:
            print(f"Error removing attendees: {error}")
            return None

    def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event

        Args:
            event_id: Google Calendar event ID

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.service:
            raise RuntimeError("Calendar service not authenticated")

        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            return True

        except HttpError as error:
            print(f"Error deleting event: {error}")
            return False

    def update_rsvp_status(
        self,
        event_id: str,
        response_status: str,
        attendee_email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update RSVP status for an event attendee

        Args:
            event_id: Google Calendar event ID
            response_status: One of 'accepted', 'declined', 'tentative', 'needsAction'
            attendee_email: Email of attendee to update (defaults to 'me' - the authenticated user)

        Returns:
            Updated event details or None if failed
        """
        if not self.service:
            raise RuntimeError("Calendar service not authenticated")

        # Validate response status
        valid_statuses = ['accepted', 'declined', 'tentative', 'needsAction']
        if response_status not in valid_statuses:
            print(f"Invalid response status. Must be one of: {', '.join(valid_statuses)}")
            return None

        try:
            # Get the authenticated user's email if not provided
            if not attendee_email:
                # Get user's primary email
                calendar = self.service.calendars().get(calendarId='primary').execute()
                attendee_email = calendar.get('id')  # Calendar ID is the user's email

            # Get existing event
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            # Update the attendee's response status
            attendees = event.get('attendees', [])
            updated = False
            
            for attendee in attendees:
                if attendee.get('email') == attendee_email:
                    attendee['responseStatus'] = response_status
                    updated = True
                    break

            # If user is not in attendees list (they're the organizer), add them
            if not updated:
                attendees.append({
                    'email': attendee_email,
                    'responseStatus': response_status,
                    'organizer': event.get('organizer', {}).get('email') == attendee_email
                })
                updated = True

            event['attendees'] = attendees

            # Update the event
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()

            return self._parse_event(updated_event)

        except HttpError as error:
            print(f"Error updating RSVP status: {error}")
            return None

    def add_google_meet(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Add a Google Meet video conference link to an existing event

        Args:
            event_id: Google Calendar event ID

        Returns:
            Updated event details with Google Meet link or None if failed
        """
        if not self.service:
            raise RuntimeError("Calendar service not authenticated")

        try:
            # Get existing event
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            # Add Google Meet conference data
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': f"meet-{event_id}",
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            }

            # Update the event with conference data
            # Must use conferenceDataVersion=1 to enable conference creation
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                conferenceDataVersion=1,
                sendUpdates='all'
            ).execute()

            return self._parse_event(updated_event)

        except HttpError as error:
            print(f"Error adding Google Meet: {error}")
            return None

    def create_event_with_meet(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new calendar event with Google Meet video conference

        Args:
            summary: Event title
            start_time: Start time (ISO format: YYYY-MM-DDTHH:MM:SS)
            end_time: End time (ISO format: YYYY-MM-DDTHH:MM:SS)
            description: Event description
            location: Event location
            attendees: List of attendee email addresses

        Returns:
            Created event details with Google Meet link or None if failed
        """
        if not self.service:
            raise RuntimeError("Calendar service not authenticated")

        try:
            event_body = {
                'summary': summary,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC',
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"meet-{start_time}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                }
            }

            if description:
                event_body['description'] = description
            
            if location:
                event_body['location'] = location
            
            if attendees:
                event_body['attendees'] = [{'email': email} for email in attendees]

            # Create event with conference data
            event = self.service.events().insert(
                calendarId='primary',
                body=event_body,
                conferenceDataVersion=1,  # Required for Google Meet
                sendUpdates='all'
            ).execute()

            return self._parse_event(event)

        except HttpError as error:
            print(f"Error creating event with Google Meet: {error}")
            return None

    def set_event_reminders(
        self,
        event_id: str,
        reminders: List[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Set notification reminders for a calendar event

        Args:
            event_id: Google Calendar event ID
            reminders: List of reminder times in minutes before event
                      (e.g., [10, 30] for 10 and 30 minutes before)

        Returns:
            Updated event details or None if failed
        """
        if not self.service:
            raise RuntimeError("Calendar service not authenticated")

        try:
            # Get existing event
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            # Set custom reminders
            event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': minutes} for minutes in reminders
                ]
            }

            # Update the event
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()

            return self._parse_event(updated_event)

        except HttpError as error:
            print(f"Error setting event reminders: {error}")
            return None

