from googleapiclient.discovery import build
import uuid

def create_meeting(service, title, date, start_time, duration=30):

    start_datetime = f"{date}T{start_time}:00"

    # simple end time logic (you can improve later)
    end_datetime = f"{date}T{start_time}:00"

    event = {
        "summary": title,
        "start": {
            "dateTime": start_datetime,
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "dateTime": end_datetime,
            "timeZone": "Asia/Kolkata"
        },
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {
                    "type": "hangoutsMeet"
                }
            }
        }
    }

    event = service.events().insert(
        calendarId="primary",
        body=event,
        conferenceDataVersion=1
    ).execute()

    return event.get("hangoutLink")