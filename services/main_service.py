"""
main_service.py — Orchestrates the full pipeline:

  Audio file
    ↓  (audio_to_json)
  AssemblyAI transcript JSON
    ↓  (json_to_summary)
  Structured AudioReport dict
    ↓  (summary_to_docx)
  .docx file
    ↓
  AudioReportResponse (JSON + download URL)
"""

import os
from services.audio_to_json import audio_to_json
from services.json_to_summary import json_to_summary
# from services.summary_to_docx import summary_to_docx

NGROK_URL   = os.environ.get("NGROK_URL", "http://localhost:8000")
REPORTS_DIR = os.environ.get("REPORTS_DIR", "reports")

async def process_audio_to_report(file) -> dict:

    # STEP 1 → Audio → JSON
    json_path = await audio_to_json(file)

    # STEP 2 → JSON → Report
    report = json_to_summary(json_path, audio_filename=file.filename)


    return {
        "success": True,
        "report": report
    }