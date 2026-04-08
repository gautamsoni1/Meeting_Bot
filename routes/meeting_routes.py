# # from fastapi import APIRouter, UploadFile, File

# # from services.audio_to_json import audio_to_json
# # from services.json_to_summary import json_to_summary
# # from services.report_generator import json_to_pdf

# # router = APIRouter()


# # @router.post("/generate-meeting-report")
# # async def generate_meeting_report(file: UploadFile = File(...)):

# #     json_path = await audio_to_json(file)

# #     report = json_to_summary(json_path, file.filename)

# #     pdf_path = json_to_pdf(report, f"{file.filename}.pdf")

# #     return {
# #         "message": "Report generated successfully",
# #         "pdf_file": pdf_path,
# #         "report_data": report
# #     }


# # routers/meeting.py  (or wherever your router lives)

# from fastapi import APIRouter, HTTPException
# from utils import store
# from services.Recall_client import create_bot
# from config.config import WEBHOOK_URL
# from models.schemas import JoinMeetingRequest   # adjust import path if needed

# router = APIRouter()


# @router.post("/start-meeting", summary="Join Meeting & Auto-Save Audio")
# async def start_meeting(data: JoinMeetingRequest):
#     """
#     Give a meeting URL.
#     The bot joins, records, and saves the MP3 automatically.
#     Poll GET /meeting-report/{bot_id} to check progress.
#     """
#     if not WEBHOOK_URL.startswith("https://"):
#         raise HTTPException(
#             status_code=500,
#             detail="❌ WEBHOOK_URL must be public HTTPS (ngrok required)",
#         )

#     result = create_bot(meeting_url=data.meeting_url, webhook_url=WEBHOOK_URL)

#     bot_id = result.get("id")
#     if not bot_id:
#         raise HTTPException(
#             status_code=500,
#             detail="Recall API did not return a bot ID.",
#         )

#     store.upsert(bot_id, status="recording", report_status="pending")

#     return {
#         "message":  "✅ Bot is joining the meeting. Audio will be saved automatically after the meeting ends.",
#         "bot_id":   bot_id,
#         "poll_url": f"/meeting-report/{bot_id}",
#     }


# @router.get("/meeting-report/{bot_id}", summary="Get Meeting Audio Status")
# async def get_meeting_report(bot_id: str):
#     """
#     Poll this endpoint after POST /start-meeting.

#     Statuses:
#       recording   → meeting in progress
#       processing  → meeting ended, downloading MP3
#       done        → ✅ MP3 saved and ready
#       error       → something failed
#     """
#     info = store.get(bot_id)
#     if not info:
#         raise HTTPException(status_code=404, detail=f"Bot '{bot_id}' not found.")

#     report_status = info.get("report_status", "pending")
#     status        = info.get("status", "unknown")

#     # ✅ Audio is ready
#     if report_status == "done":
#         return {
#             "bot_id":        bot_id,
#             "status":        status,
#             "report_status": "done",
#             "message":       "✅ Audio is ready!",
#             "mp3_url":       info.get("public_url"),
#         }

#     # ❌ Something went wrong
#     if status == "error" or report_status == "error":
#         return {
#             "bot_id":        bot_id,
#             "status":        "error",
#             "report_status": report_status,
#             "message":       "❌ Something failed. Check server logs.",
#         }

#     # ⏳ Still in progress
#     return {
#         "bot_id":        bot_id,
#         "status":        status,
#         "report_status": report_status,
#         "message":       "⏳ Still working... keep polling every 15 seconds.",
#     }








import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from config.config import WEBHOOK_URL, NGROK_URL, RECORDINGS_DIR
from services.Recall_client import create_bot, get_mixed_audio_url
from utils import store
from utils.store import upsert, get
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


# ── Request Model ─────────────────────────────────────────────────────────────

class JoinMeetingRequest(BaseModel):
    meeting_url: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"meeting_url": "https://meet.google.com/xxx-yyyy-zzz"}
            ]
        }
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/join-meeting", summary="Join Meeting")
async def join_meeting(data: JoinMeetingRequest):
    """
    Send a bot to a Zoom / Google Meet / Teams meeting.
    webhook_url is auto-set from .env NGROK_URL.

    Flow:
      1. POST /join-meeting             → get bot_id
      2. Poll GET /status/{bot_id}      → wait for status == "done"
      3. GET  /recording/{bot_id}       → get download info + download_url
      4. GET  /download/{bot_id}.mp3    → actual MP3 file download
    """
    print(f"🚀 Joining meeting : {data.meeting_url}")

    if not WEBHOOK_URL.startswith("https://"):
        raise HTTPException(
            status_code=500,
            detail="❌ WEBHOOK_URL must be public HTTPS (ngrok required)"
        )

    print(f"   Webhook URL     : {WEBHOOK_URL}")

    result = create_bot(
        meeting_url=data.meeting_url,
        webhook_url=WEBHOOK_URL,
    )

    bot_id = result.get("id")
    if not bot_id:
        raise HTTPException(
            status_code=500,
            detail="Recall API did not return a bot ID. Check your API key and meeting URL.",
        )

    store.upsert(bot_id, status="recording")

    return {
        "message": "✅ Bot is joining the meeting",
        "bot_id": bot_id,
        "status_url": f"/status/{bot_id}",
        "recording_url": f"/recording/{bot_id}",
        "data": result,
    }


@router.get("/status/{bot_id}", summary="Poll Bot Status")
async def get_status(bot_id: str):
    """
    Poll this endpoint every 10–15s after joining.

    Statuses:
      recording   → meeting in progress
      processing  → meeting ended, downloading MP3 in background (webhook triggered)
      done        → ✅ MP3 saved to recordings/ folder, call GET /recording/{bot_id}
      error       → something failed
    """
    info = get(bot_id)
    if not info:
        raise HTTPException(status_code=404, detail="Bot not found")

    current_status = info.get("status")

    # ── Webhook already handled everything — just return current state ────────
    if current_status in ("done", "processing", "error"):
        return {"bot_id": bot_id, **info}

    # ── Still recording: lightweight Recall API check as fallback ─────────────
    try:
        mp3_url = get_mixed_audio_url(bot_id)
        if mp3_url:
            # CDN URL is ready but webhook handles the actual download
            upsert(bot_id, mp3_download_url=mp3_url)
        else:
            upsert(bot_id, status="recording")
    except Exception as e:
        print(f"[status] ERROR polling Recall: {e}")

    return {"bot_id": bot_id, **get(bot_id)}


@router.get("/recording/{bot_id}", summary="Get Recording Info & Download Link")
async def get_recording(bot_id: str):
    """
    Returns recording info once meeting has ended.
    Only returns a download_url after status == "done".

    Use the returned download_url to download the actual MP3.
    """
    info = store.get(bot_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Bot ID '{bot_id}' not found.")

    if info["status"] == "error":
        return {
            "bot_id": bot_id,
            "status": "error",
            "message": "❌ Recording failed. Check server logs.",
            "download_url": None,
        }

    if info["status"] != "done":
        return {
            "bot_id": bot_id,
            "status": info["status"],
            "message": "⏳ Recording not ready yet. Keep polling GET /status/{bot_id}",
            "download_url": None,
        }

    # ── Build download URL ────────────────────────────────────────────────────
    local_file = info.get("local_file")
    filename = f"{bot_id}.mp3"

    if local_file and os.path.exists(local_file):
        # Serve from local recordings/ folder via /download/ route
        download_url = f"{NGROK_URL}/download/{filename}" if NGROK_URL else f"/download/{filename}"
    else:
        # Fallback: point to Recall CDN URL if local file missing
        download_url = info.get("mp3_download_url")

    if not download_url:
        return {
            "bot_id": bot_id,
            "status": "done",
            "message": "⚠️ Status is done but no file found. Check server logs.",
            "download_url": None,
        }

    return {
        "bot_id": bot_id,
        "status": "done",
        "message": "✅ Recording ready!",
        "download_url": download_url,
        "recall_cdn_url": info.get("mp3_download_url"),
        "local_file": local_file,
    }


@router.get("/download/{filename}", summary="Download Recorded MP3")
async def download_recording(filename: str):
    """
    Streams the saved MP3 file directly from the recordings/ folder.

    filename format : {bot_id}.mp3
    Example         : GET /download/abc123def456.mp3

    Steps to reach here:
      1. POST /join-meeting
      2. Poll GET /status/{bot_id}  →  wait for status == "done"
      3. GET  /recording/{bot_id}   →  grab download_url
      4. GET  /download/{bot_id}.mp3 ← you are here
    """
    # ── Security checks ───────────────────────────────────────────────────────
    if not filename.endswith(".mp3"):
        raise HTTPException(status_code=400, detail="Only .mp3 files are served here.")

    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = os.path.join(RECORDINGS_DIR, filename)

    print(f"📥 Download request : {filename}")
    print(f"   File path        : {file_path}")
    print(f"   File exists      : {os.path.exists(file_path)}")

    # ── Debug: list recordings dir if file missing ────────────────────────────
    if not os.path.exists(file_path):
        try:
            existing = os.listdir(RECORDINGS_DIR)
            print(f"   Files in recordings/ : {existing}")
        except Exception as e:
            print(f"   Could not list recordings dir: {e}")

        raise HTTPException(
            status_code=404,
            detail=(
                f"File '{filename}' not found in recordings/ folder. "
                f"Recording may still be processing — poll /status/{{bot_id}} first."
            )
        )

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )