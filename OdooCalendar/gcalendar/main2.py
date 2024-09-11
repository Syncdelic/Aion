import datetime as dt
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def main():
    creds = None

    # Load credentials from the token.json file, if it exists
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no valid credentials, or if they are expired, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Initialize the Calendar API
        service = build("calendar", "v3", credentials=creds)

        # Define the event details
        event = {
            "summary": "Consulta",
            "location": "Guadalajara, Jalisco, Mexico",
            "description": "Implementación de chatbot para consultas médicas",
            "colorId": "2",
            "start": {
                "dateTime": "2024-09-16T09:00:00-05:00",  
                "timeZone": "America/Mexico_City",
            },
            "end": {
                "dateTime": "2024-09-16T10:00:00-05:00",  
                "timeZone": "America/Mexico_City",
            },
            "recurrence": [
                "RRULE:FREQ=DAILY;COUNT=1",
            ],
            "attendees": [
                {"email": "arrc.psy@gmail.com"},
            ],
        }

        # Insert the event into the primary calendar
        event = service.events().insert(calendarId="primary", body=event).execute()

        print(f"Event created: {event.get('htmlLink')}")

    except HttpError as error:
        print("Error: ", error)

if __name__ == "__main__":
    main()

