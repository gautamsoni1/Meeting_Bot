"""
transcribe.py — Auto-transcribe from recordings/ folder

3 ways to use:

  1. Latest file (most recent MP3):
       result = await transcribe_latest()

  2. Specific bot_id:
       result = await transcribe_by_bot_id("f6f4258a-f73b-458b-80cb-09554bc6a499")

  3. Specific file path:
       result = await transcribe_file("recordings/myfile.mp3")
"""

import requests
import os
import json
import time
from services.json_to_summary import json_to_summary
from services.report_generator import json_to_pdf
from config.config import (
    ASSEMBLY_UPLOAD_URL,
    ASSEMBLY_TRANSCRIPT_URL,
    RECORDINGS_DIR,
    get_assembly_headers
)

TRANSCRIPT_DIR = "transcripts"
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)


# ── Core: transcribe any local file path ─────────────────────────────────────

async def transcribe_file(file_path: str) -> str:
    """
    Transcribe a local MP3 file using AssemblyAI.
    Returns path to saved JSON transcript.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ File not found: {file_path}")

    headers = get_assembly_headers()
    filename = os.path.basename(file_path)

    print(f"\n🎙️  Starting transcription")
    print(f"   File : {file_path}")
    print(f"   Size : {os.path.getsize(file_path) / (1024*1024):.2f} MB\n")

    # ── STEP 1: Upload to AssemblyAI ──────────────────────────────────────────
    print("🔼 Uploading to AssemblyAI ...")
    with open(file_path, "rb") as f:
        upload_res = requests.post(
            ASSEMBLY_UPLOAD_URL,
            headers=headers,
            data=f,
            timeout=120
        )

    print(f"   Upload status : {upload_res.status_code}")

    if upload_res.status_code != 200:
        raise Exception(f"Upload failed: {upload_res.text}")

    upload_data = upload_res.json()
    if "upload_url" not in upload_data:
        raise Exception(f"Invalid upload response: {upload_data}")

    audio_url = upload_data["upload_url"]
    print(f"   Uploaded OK   : {audio_url[:60]}...")

    # ── STEP 2: Request transcription ─────────────────────────────────────────
    print("\n📝 Requesting transcription ...")
    transcript_res = requests.post(
        ASSEMBLY_TRANSCRIPT_URL,
        json={
            "audio_url": audio_url,
            "speech_models": ["universal-2"],
            "speaker_labels": True,
        },
        headers=headers,
        timeout=30
    )

    print(f"   Transcript status : {transcript_res.status_code}")

    if transcript_res.status_code != 200:
        raise Exception(f"Transcription request failed: {transcript_res.text}")

    transcript_data = transcript_res.json()
    if "id" not in transcript_data:
        raise Exception(f"Invalid transcript response: {transcript_data}")

    transcript_id = transcript_data["id"]
    print(f"   Transcript ID     : {transcript_id}")

    # ── STEP 3: Poll until done ───────────────────────────────────────────────
    print("\n⏳ Waiting for transcription to complete ...")
    attempt = 0
    while True:
        attempt += 1
        time.sleep(3)

        polling = requests.get(
            f"{ASSEMBLY_TRANSCRIPT_URL}/{transcript_id}",
            headers=headers,
            timeout=30
        )

        if polling.status_code != 200:
            raise Exception(f"Polling failed: {polling.text}")

        polling_data = polling.json()
        status = polling_data.get("status")

        print(f"   [{attempt}] status = {status}")

        if status == "completed":
            print("✅ Transcription completed!")
            break
        elif status == "error":
            raise Exception(f"Transcription failed: {polling_data.get('error')}")

    # ── STEP 4: Save JSON ─────────────────────────────────────────────────────
    base_name       = os.path.splitext(filename)[0]
    json_filename   = f"{base_name}_{int(time.time())}.json"
    json_path       = os.path.join(TRANSCRIPT_DIR, json_filename)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(polling_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Transcript saved : {json_path}\n")
    
    # ✅ STEP 5: GENERATE STRUCTURED SUMMARY
    print("🧠 Generating AI summary...")
    
    try:
        report_json = json_to_summary(json_path, filename)
        print("✅ Summary generated")
    except Exception as e:
        print(f"❌ Summary failed: {e}")
        report_json = None
    
    # ✅ STEP 6: GENERATE PDF
    if report_json:
        print("📄 Generating PDF report...")
    
        try:
            pdf_path = json_to_pdf(report_json, filename=f"{base_name}.pdf")
            print(f"✅ PDF Generated: {pdf_path}")
        except Exception as e:
            print(f"❌ PDF Generation Failed: {e}")
    
    return json_path


# ── Helper: pick latest MP3 from recordings/ folder ──────────────────────────

def get_latest_recording() -> str:
    """
    Returns the path of the most recently modified MP3
    in the recordings/ folder.
    Raises FileNotFoundError if folder is empty.
    """
    mp3_files = [
        os.path.join(RECORDINGS_DIR, f)
        for f in os.listdir(RECORDINGS_DIR)
        if f.endswith(".mp3")
    ]

    if not mp3_files:
        raise FileNotFoundError(
            f"❌ No MP3 files found in {RECORDINGS_DIR}\n"
            f"   Make sure the meeting has ended and the bot has finished recording."
        )

    # Sort by last-modified time, newest first
    mp3_files.sort(key=os.path.getmtime, reverse=True)
    latest = mp3_files[0]

    print(f"📂 Found {len(mp3_files)} recording(s) in {RECORDINGS_DIR}/")
    print(f"   Using latest : {os.path.basename(latest)}")
    print(f"   Modified     : {time.ctime(os.path.getmtime(latest))}")

    return latest


# ── Public API ────────────────────────────────────────────────────────────────

async def transcribe_latest() -> str:
    """
    Auto-pick the most recent MP3 from recordings/ and transcribe it.
    Returns path to saved JSON transcript.

    Usage:
        json_path = await transcribe_latest()
    """
    file_path = get_latest_recording()
    return await transcribe_file(file_path)


async def transcribe_by_bot_id(bot_id: str) -> str:
    """
    Transcribe the recording for a specific bot_id.
    Looks for recordings/{bot_id}.mp3

    Usage:
        json_path = await transcribe_by_bot_id("f6f4258a-...")
    """
    file_path = os.path.join(RECORDINGS_DIR, f"{bot_id}.mp3")
    return await transcribe_file(file_path)


# ── Optional: list all available recordings ───────────────────────────────────

def list_recordings() -> list[dict]:
    """
    Returns a list of all MP3s in recordings/ with metadata.
    Sorted newest first.

    Usage:
        recordings = list_recordings()
        for r in recordings:
            print(r["filename"], r["size_mb"], r["modified"])
    """
    files = []
    for f in os.listdir(RECORDINGS_DIR):
        if not f.endswith(".mp3"):
            continue
        full_path = os.path.join(RECORDINGS_DIR, f)
        files.append({
            "filename" : f,
            "bot_id"   : f.replace(".mp3", ""),
            "path"     : full_path,
            "size_mb"  : round(os.path.getsize(full_path) / (1024 * 1024), 2),
            "modified" : time.ctime(os.path.getmtime(full_path)),
        })

    files.sort(key=lambda x: os.path.getmtime(x["path"]), reverse=True)
    return files

