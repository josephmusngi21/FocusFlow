from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class GoogleCalendarIntegration:
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, credentials_file: str = None, calendar_id: str = "primary"):
        self.credentials_file = credentials_file or os.getenv("GOOGLE_CALENDAR_CREDENTIALS_FILE")
        self.calendar_id = calendar_id or os.getenv("GOOGLE_CALENDAR_ID", "primary")
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        token_file = "token.pickle"
        
        if not self.credentials_file:
            logger.warning("Google Calendar credentials file not configured")
            return

        # Load existing token
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)

        # If there are no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh Google Calendar credentials: {e}")
                    return
            else:
                if not os.path.exists(self.credentials_file):
                    logger.warning(f"Google Calendar credentials file not found: {self.credentials_file}")
                    return
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Failed to authenticate with Google Calendar: {e}")
                    return

            # Save credentials for next run
            try:
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                logger.error(f"Failed to save Google Calendar token: {e}")

        try:
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Calendar")
        except Exception as e:
            logger.error(f"Failed to build Google Calendar service: {e}")

    def is_available(self) -> bool:
        """Check if Google Calendar integration is available"""
        return self.service is not None

    def create_event(self, title: str, start_time: str, end_time: str, date: str, description: str = None) -> Optional[str]:
        """Create a calendar event"""
        if not self.is_available():
            logger.warning("Google Calendar integration not available")
            return None

        try:
            # Convert time strings to ISO format
            start_datetime = f"{date}T{start_time}:00"
            end_datetime = f"{date}T{end_time}:00"

            event = {
                'summary': title,
                'description': description or '',
                'start': {
                    'dateTime': start_datetime,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_datetime,
                    'timeZone': 'UTC',
                },
                'source': {
                    'title': 'FocusFlow Task Optimizer',
                    'url': 'https://github.com/josephmusngi21/FocusFlow'
                }
            }

            created_event = self.service.events().insert(
                calendarId=self.calendar_id, body=event).execute()
            
            logger.info(f"Created Google Calendar event: {created_event.get('id')}")
            return created_event.get('id')

        except Exception as e:
            logger.error(f"Failed to create Google Calendar event: {e}")
            return None

    def update_event(self, event_id: str, title: str = None, start_time: str = None, 
                    end_time: str = None, date: str = None, description: str = None) -> bool:
        """Update an existing calendar event"""
        if not self.is_available():
            return False

        try:
            # Get the existing event
            event = self.service.events().get(
                calendarId=self.calendar_id, eventId=event_id).execute()

            # Update fields if provided
            if title:
                event['summary'] = title
            if description is not None:
                event['description'] = description
            if start_time and end_time and date:
                event['start']['dateTime'] = f"{date}T{start_time}:00"
                event['end']['dateTime'] = f"{date}T{end_time}:00"

            updated_event = self.service.events().update(
                calendarId=self.calendar_id, eventId=event_id, body=event).execute()
            
            logger.info(f"Updated Google Calendar event: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update Google Calendar event: {e}")
            return False

    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event"""
        if not self.is_available():
            return False

        try:
            self.service.events().delete(
                calendarId=self.calendar_id, eventId=event_id).execute()
            
            logger.info(f"Deleted Google Calendar event: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete Google Calendar event: {e}")
            return False

    def sync_schedule(self, schedule_items: List[dict]) -> List[str]:
        """Sync schedule items to Google Calendar"""
        if not self.is_available():
            logger.warning("Google Calendar not available for sync")
            return []

        event_ids = []
        for item in schedule_items:
            event_id = self.create_event(
                title=item['task_title'],
                start_time=item['scheduled_start'],
                end_time=item['scheduled_end'],
                date=item['date'],
                description=f"Task scheduled by FocusFlow\nEnergy Cost: {item['energy_cost']}"
            )
            if event_id:
                event_ids.append(event_id)

        logger.info(f"Synced {len(event_ids)} events to Google Calendar")
        return event_ids

    def get_busy_times(self, date: str, time_min: str = "08:00", time_max: str = "18:00") -> List[dict]:
        """Get busy times from calendar for the given date"""
        if not self.is_available():
            return []

        try:
            # Convert to ISO format
            start_datetime = f"{date}T{time_min}:00Z"
            end_datetime = f"{date}T{time_max}:00Z"

            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_datetime,
                timeMax=end_datetime,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            busy_times = []

            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Extract time from datetime strings
                if 'T' in start:
                    start_time = start.split('T')[1][:5]
                    end_time = end.split('T')[1][:5]
                    
                    busy_times.append({
                        'start': start_time,
                        'end': end_time,
                        'title': event.get('summary', 'Busy')
                    })

            logger.info(f"Found {len(busy_times)} busy times for {date}")
            return busy_times

        except Exception as e:
            logger.error(f"Failed to get busy times from Google Calendar: {e}")
            return []