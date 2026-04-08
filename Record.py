"""
record.py — Drop-in auto-recorder
Usage: python record.py <meeting_url>
       python record.py https://meet.google.com/xxx-yyy-zzz

What it does (no routes, no webhook, no server needed):
  1. Sends a Recall.ai bot to the meeting
  2. Polls until the meeting ends and the MP3 is ready
  3. Downloads the MP3 → recordings/{bot_id}.mp3

Requirements:
  pip install requests python-dotenv

.env must contain:
  RECALL_API_KEY=Token <your_key>
  BASE_URL=https://us-west-2.recall.ai/api/v1  (optional, has default)
"""

import asyncio
from services.audio_to_json import transcribe_by_bot_id
import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

RECALL_API_KEY = os.getenv("RECALL_API_KEY")
BASE_URL       = os.getenv("BASE_URL", "https://us-west-2.recall.ai/api/v1").rstrip("/")
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")

POLL_INTERVAL  = 15    # seconds between status checks
MAX_WAIT_HOURS = 4     # give up after this many hours
MAX_POLLS      = int((MAX_WAIT_HOURS * 3600) / POLL_INTERVAL)

if not RECALL_API_KEY:
    raise RuntimeError("❌ RECALL_API_KEY missing from .env")

os.makedirs(RECORDINGS_DIR, exist_ok=True)


# ── Recall API helpers ────────────────────────────────────────────────────────

def _headers() -> dict:
    return {
        "Authorization": RECALL_API_KEY,
        "Content-Type":  "application/json",
        "accept":        "application/json",
    }


def create_bot(meeting_url: str) -> str:
    """Send a bot to the meeting. Returns bot_id."""
    payload = {
        "meeting_url": meeting_url,
        "bot_name":    "Meeting Recorder",
        "recording_config": {
            "audio_mixed_mp3": {},
        },
    }
    resp = requests.post(f"{BASE_URL}/bot/", json=payload, headers=_headers(), timeout=30)
    print(f"[create_bot] status={resp.status_code}")
    resp.raise_for_status()
    bot_id = resp.json().get("id")
    if not bot_id:
        raise RuntimeError(f"❌ No bot_id in response: {resp.text}")
    print(f"✅ Bot created  →  bot_id = {bot_id}")
    return bot_id


def get_mp3_url(bot_id: str) -> str | None:
    """
    Fetch the bot and return the MP3 CDN URL once ready.
    Returns None if the recording isn't done yet.
    """
    resp = requests.get(f"{BASE_URL}/bot/{bot_id}/", headers=_headers(), timeout=30)
    resp.raise_for_status()
    bot = resp.json()

    status_changes = bot.get("status_changes", [])
    if status_changes:
        latest = status_changes[-1].get("code", "")
        print(f"   bot status = {latest}")

    for recording in bot.get("recordings", []):
        audio = recording.get("media_shortcuts", {}).get("audio_mixed")
        if not audio:
            continue
        code = audio.get("status", {}).get("code")
        print(f"   audio_mixed status = {code}")
        if code == "done":
            url = audio.get("data", {}).get("download_url")
            if url:
                return url
    return None


def poll_until_mp3_ready(bot_id: str) -> str:
    """
    Block until the MP3 is available on the Recall CDN.
    Returns the CDN download URL.
    """
    print(f"\n⏳ Waiting for meeting to end and MP3 to be ready ...")
    print(f"   (polling every {POLL_INTERVAL}s, up to {MAX_WAIT_HOURS}h)\n")

    for attempt in range(1, MAX_POLLS + 1):
        elapsed_min = (attempt * POLL_INTERVAL) // 60
        print(f"   [{attempt}/{MAX_POLLS}] {elapsed_min}m elapsed — checking ...")

        try:
            url = get_mp3_url(bot_id)
            if url:
                print(f"\n✅ MP3 ready on CDN!")
                return url
        except requests.HTTPError as e:
            print(f"   ⚠️  HTTP error: {e} — will retry")
        except Exception as e:
            print(f"   ⚠️  Error: {e} — will retry")

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(f"❌ MP3 never became ready after {MAX_WAIT_HOURS} hours")


def download_mp3(url: str, bot_id: str) -> str:
    """Stream-download the MP3 to recordings/{bot_id}.mp3. Returns local path."""
    filename    = f"{bot_id}.mp3"
    output_path = os.path.join(RECORDINGS_DIR, filename)

    print(f"\n⬇️  Downloading MP3 ...")
    print(f"   Save path : {output_path}")

    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            downloaded = 0
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
            print(f"   Downloaded : {downloaded / (1024*1024):.2f} MB")

    if not os.path.exists(output_path):
        raise RuntimeError(f"❌ File not saved: {output_path}")
    if os.path.getsize(output_path) == 0:
        raise RuntimeError(f"❌ File is empty: {output_path}")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n🎉 Recording saved!")
    print(f"   File : {output_path}")
    print(f"   Size : {size_mb:.2f} MB\n")
    return output_path


# ── Main entry point ──────────────────────────────────────────────────────────

# def record(meeting_url: str) -> str:
#     """
#     Full pipeline:
#       meeting_url  →  recordings/{bot_id}.mp3

#     Returns the local file path of the saved MP3.
#     """
#     print(f"\n🚀 Starting auto-record for: {meeting_url}\n")

#     bot_id   = create_bot(meeting_url)
#     mp3_url  = poll_until_mp3_ready(bot_id)
#     mp3_path = download_mp3(mp3_url, bot_id)

#     return mp3_path

def record(meeting_url: str) -> str:
    """
    Full pipeline:
      meeting_url → recordings/{bot_id}.mp3 → transcripts/{json}
    """

    print(f"\n🚀 Starting auto-record for: {meeting_url}\n")

    # Step 1: Create bot
    bot_id = create_bot(meeting_url)

    # Step 2: Wait for recording
    mp3_url = poll_until_mp3_ready(bot_id)

    # Step 3: Download MP3
    mp3_path = download_mp3(mp3_url, bot_id)

    # ✅ Step 4: Automatically transcribe
    print("\n🎯 Starting auto-transcription...\n")

    try:
        json_path = asyncio.run(transcribe_by_bot_id(bot_id))
        print(f"\n✅ Transcription Done: {json_path}")
    except Exception as e:
        print(f"❌ Transcription Failed: {e}")

    return mp3_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python record.py <meeting_url>")
        print("Example: python record.py https://meet.google.com/xxx-yyy-zzz")
        sys.exit(1)

    meeting_url = sys.argv[1]
    output_file = record(meeting_url)
    print(f"✅ Done: {output_file}")