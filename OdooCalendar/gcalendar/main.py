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

        # Get the current time as a timezone-aware datetime object in UTC
        now = dt.datetime.now(dt.timezone.utc).isoformat()

        # Fetch the next 10 events on the user's primary calendar
        event_result = service.events().list(
            calendarId="primary", timeMin=now,
            maxResults=10, singleEvents=True,
            orderBy="startTime").execute()

        events = event_result.get("items", [])

        if not events:
            print("No upcoming events")
            return

        # Print each event's start time and summary
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])

    except HttpError as error:
        print("Error: ", error)

if __name__ == "__main__":
    main()

