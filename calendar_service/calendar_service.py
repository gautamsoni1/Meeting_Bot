from googleapiclient.discovery import build
import uuid

def create_meeting(creds, title, date, time):
    """
    Creates a Google Calendar event and returns both the 
    Meeting URL and the Event ID.
    """
    # 1. Build the Google Calendar service using your credentials
    service = build("calendar", "v3", credentials=creds)

    # 2. Format the start and end time (using the same for both as a placeholder)
    start_time = f"{date}T{time}:00"
    
    # 3. Define the event details
    event_body = {
        "summary": title,
        "start": {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"}
            }
        }
    }

    # 4. Insert the event into the primary calendar
    # conferenceDataVersion=1 is required to generate the Google Meet link
    event = service.events().insert(
        calendarId="primary",
        body=event_body,
        conferenceDataVersion=1
    ).execute()

    # 5. Extract the Google Meet URL and the unique Calendar Event ID
    meeting_link = event.get("hangoutLink")
    event_id = event.get("id")

    # 6. Return both values (Recall.ai needs both to map emails)
    return meeting_link, event_id
