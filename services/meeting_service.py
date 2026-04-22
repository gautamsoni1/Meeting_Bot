import os
import re
import uuid
import datetime

from state.chat_state import set_state, get_state, clear_state
from db.mongo import report_collection, meeting_collection
from config.config import NGROK_URL
from services.scheduler_service import add_scheduled_meeting


def handle_meeting(user_id, message):

    msg = message.lower().strip()
    state = get_state(user_id)

    # =========================
    # 📄 REPORT FLOW
    # =========================

    if "report" in msg or "pdf" in msg:

        report = report_collection.find_one(
        {"user_id": user_id},
            sort=[("created_at", -1)]
        )
    
        if not report:
            return {"message": "⏳ No report found yet"}
    
        pdf_path = report.get("pdf_report_path")
    
        if not pdf_path:
            return {"message": "❌ PDF not generated yet"}
    
        pdf_url = f"{NGROK_URL}/reports/{os.path.basename(pdf_path)}"
    
        # 🔥 NEW STATE (ASK CONFIRMATION FIRST)
        set_state(user_id, {
            "step": "ask_pdf_confirm",
            "pdf_path": pdf_path
        })
    
        return {
            "message": f"""📄 Report ready  
    👉 {pdf_url}
    
    ❓ Do you want to ask questions from this PDF? (yes/no)"""
        }

    # =========================
    # 📚 PDF QA MODE
    # =========================
    if state and state.get("step") == "pdf_qa":

        from services.pdf_qa_service import ask_pdf, vector_store, create_vector_db

        if user_id not in vector_store:
            create_vector_db(user_id, state["pdf_path"])

        if msg in ["exit", "stop"]:
            clear_state(user_id)
            vector_store.pop(user_id, None)
            return {"message": "❌ Exited QA mode"}

        return {"message": ask_pdf(user_id, message)}

    # =========================
    # 📅 MEETING CREATION
    # =========================
    if "meeting" in msg:

        from services.parser import parse_meeting
        from auth.token_service import get_token
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        import datetime

        parsed = parse_meeting(user_id, message)

        if not parsed:
            return {"message": "❌ Could not understand meeting"}

        date = parsed.get("date", "").strip()
        time = parsed.get("time", "").strip()

        if not date or not time:
            return {"message": "⏰ Missing date/time"}

        # fix spacing issues in time
        time = re.sub(r"\s+", " ", time).strip()

        try:
            start = datetime.datetime.strptime(
                f"{date} {time}",
                "%Y-%m-%d %H:%M"
            )
        except Exception as e:
            return {"message": f"❌ Time error: {str(e)}"}

        end = start + datetime.timedelta(minutes=parsed.get("duration", 30))

        token = get_token(user_id)

        if not token:
            return {"message": "❌ Google not connected"}

        creds = Credentials(
            token=token["access_token"],
            refresh_token=token["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=token["client_id"],
            client_secret=token["client_secret"]
        )

        service = build("calendar", "v3", credentials=creds)

        # =========================
        # CREATE GOOGLE EVENT
        # =========================
        event = service.events().insert(
            calendarId="primary",
            body={
                "summary": parsed["title"],
                "start": {
                    "dateTime": start.isoformat(),
                    "timeZone": "Asia/Kolkata"
                },
                "end": {
                    "dateTime": end.isoformat(),
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
            },
            conferenceDataVersion=1
        ).execute()

        meeting_url = event.get("hangoutLink")
        event_id = event.get("id")

        # =========================
        # ✅ FIX: GET PARTICIPANTS SAFELY
        # =========================
        participants = []

        try:
            attendees = event.get("attendees", [])
            participants = [
                a.get("email")
                for a in attendees
                if isinstance(a, dict) and a.get("email")
            ]
        except Exception as e:
            print("⚠️ participant extract error:", e)

        # =========================
        # SAVE MEETING
        # =========================
        meeting_collection.insert_one({
            "user_id": user_id,
            "event_id": event_id,
            "meeting_url": meeting_url,
            "participants": participants,   # ✅ FIXED
            "created_at": datetime.datetime.utcnow()
        })

        # =========================
        # SAVE STATE
        # =========================
        set_state(user_id, {
            "step": "record_confirm",
            "meeting_url": meeting_url,
            "event_id": event_id,
            "start_time": start.isoformat()
        })

        return {
            "message": f"📅 Meeting created\n👉 {meeting_url}\n\nBot join & record? (yes/no)"
        }

    # =========================
    # 🤖 BOT RECORD CONFIRM
    # =========================
    if state and state.get("step") == "record_confirm":

        meeting_url = state["meeting_url"]
        event_id = state["event_id"]

        if msg == "yes":

            add_scheduled_meeting(
                job_id=event_id,
                meeting_url=meeting_url,
                scheduled_at_iso=state["start_time"],
                user_id=user_id
            )

            clear_state(user_id)

            return {
                "message": f"🤖 Bot scheduled\n👉 {meeting_url}"
            }

        if msg == "no":

            clear_state(user_id)

            return {
                "message": f"👍 Meeting created only\n👉 {meeting_url}"
            }

        return {"message": "Please reply YES or NO"}

    return {"message": "Type: meeting or report"}