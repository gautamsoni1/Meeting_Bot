"""
json_to_summary.py — Step 2 of pipeline (FINAL STABLE VERSION)
"""

import json
import re
from datetime import datetime
from groq import Groq
from config.config import GROQ_API_KEY


# ─────────────────────────────────────────────
# PROMPT (STRICT JSON + PARAGRAPH SUMMARY)
# ─────────────────────────────────────────────

SUMMARY_SYSTEM = """
You are a professional meeting report generator.

You MUST return ONLY valid JSON in the exact structure below.

{
  "title": "string",

#   "participants": [
#     {"name": "string", "role": "string"}
#   ],

    "participants": [
   {
     "name": "Gautam Soni"
   },
   {
     "name": "Rahul"
   },  {"role": "string"},
   ],

  "summary": "A detailed professional paragraph",

  "discussion_sections": [
    {
      "type": "status_update | planning | problem_solving | decision",
      "title": "string",
      "speaker": "string",
      "description": "clear explanation",
      "points": ["point1", "point2"],
      "progress_percent": number (0-100),
      "risk_level": "low | medium | high"
    }
  ],

  "key_decisions": ["string"],

  "action_items": [
    {
      "owner": "string",
      "task": "string",
      "deadline": "optional",
      "priority": "high | medium | low"
    }
  ],

  "risks": [
    {
      "risk": "string",
      "impact": "high | medium | low",
      "solution": "string"
    }
  ]
}

STRICT RULES:
- Do NOT return empty fields
- Do NOT use "General discussion"
- Extract real names from transcript
- If role not known → use "Participant"
- Always include at least:
  - 3 discussion_sections
  - 2 action_items
  - 2 decisions
- Return ONLY JSON (no text, no explanation)
""".strip()



def fix_incomplete_json(text: str) -> str:
    text = re.sub(r"```(?:json)?|```", "", text).strip()

    # Fix missing }
    open_braces = text.count("{")
    close_braces = text.count("}")
    if close_braces < open_braces:
        text += "}" * (open_braces - close_braces)

    # Fix missing ]
    open_brackets = text.count("[")
    close_brackets = text.count("]")
    if close_brackets < open_brackets:
        text += "]" * (open_brackets - close_brackets)

    return text

# ─────────────────────────────────────────────
# SAFE JSON PARSER
# ─────────────────────────────────────────────

def _parse_groq_json(raw: str) -> dict:
    try:
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        return json.loads(clean)
    except Exception:
        return {}


# ─────────────────────────────────────────────
# CLEAN LIST
# ─────────────────────────────────────────────

def clean_list(items, limit=8):
    if not isinstance(items, list):
        return []

    cleaned = []
    seen = set()

    for item in items:
        item = str(item).strip()
        if item and item not in seen:
            cleaned.append(item)
            seen.add(item)

    return cleaned[:limit]


# ─────────────────────────────────────────────
# MAIN FUNCTION (FINAL)
# ─────────────────────────────────────────────

def json_to_summary(json_path: str, audio_filename: str = "audio_file") -> dict:

    client = Groq(api_key=GROQ_API_KEY)
    def detect_language_name(lang_code: str) -> str:
        mapping = {
            "en": "English",
            "hi": "Hindi",
            "fr": "French",
            "es": "Spanish",
            "de": "German",
            "it": "Italian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "ru": "Russian"
        }
        return mapping.get(lang_code, f"Unknown ({lang_code})")
    # Load transcript
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    transcript_text = data.get("text", "").strip()
    if not transcript_text:
        raise ValueError("No transcript text found")

    transcript_id  = data.get("id")
    audio_duration = data.get("audio_duration")
    language_code = data.get("language_code", "en")
    language = detect_language_name(language_code)
    word_count     = len(transcript_text.split())

    # 🚨 HANDLE SHORT AUDIO (VERY IMPORTANT)
    if word_count < 20:
        return {
            "meta": {
                "audio_filename": audio_filename,
                "meeting_of_seconds": audio_duration,
                "word_count": word_count,
                "language": language,
                "generated_at": datetime.now().isoformat(),
                "transcript_id": transcript_id
            },
            "title": "Short Audio Detected",
            "summary": "The provided audio is too short to generate a meaningful meeting report.",
            "key_topics": [],
            "action_items": [],
            "transcript_text": transcript_text,
            "speakers": None,
            "docx_path": None,
            "docx_download_url": None
        }

    # Speakers (optional)
    utterances = data.get("utterances") or []
    speakers = []
    speaker_map = {}
    
    for u in utterances:
       spk = u.get("speaker", "Unknown")

    if spk not in speaker_map:
        speaker_map[spk] = f"Speaker {spk}"

    speakers.append({
        # "speaker": spk,  
        "speaker": speaker_map[spk], # 🔥 IMPORTANT (store original first)
        "start_time": round(u.get("start", 0) / 1000, 2),
        "end_time": round(u.get("end", 0) / 1000, 2),
        "text": u.get("text", "")
    })

    # ── CALL GROQ ─────────────────────────────
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM},
                {"role": "user", "content": transcript_text[:4000]}
            ],
            temperature=0.3,
            max_completion_tokens=1500
        )

        raw = response.choices[0].message.content
        cleaned = fix_incomplete_json(raw)
        ai_data = _parse_groq_json(cleaned)

        # 🔥 MAP SPEAKERS TO REAL NAMES
        participants = ai_data.get("participants", [])
        
        names = [p.get("name") for p in participants if isinstance(p, dict)]
        
        for i, key in enumerate(speaker_map.keys()):
            if i < len(names):
                speaker_map[key] = names[i]

        # 🚨 STRICT VALIDATION
        # if not isinstance(ai_data, dict) or not ai_data:
        #     raise ValueError(f"Invalid JSON from Groq:\n{raw}")
        if not isinstance(ai_data, dict) or not ai_data:
           print("⚠️ RAW GROQ OUTPUT:\n", raw)
    
           ai_data = {
               "title": "Meeting Report",
               "participants": [],
               "summary": transcript_text[:500],
               "discussion_sections": [],
               "key_decisions": [],
               "action_items": [],
               "risks": []
           }

    except Exception as e:
        raise RuntimeError(f"Groq error: {e}")

    # ── SAFE EXTRACTION ───────────────────────
    title = str(ai_data.get("title", "Meeting Summary")).strip()

    summary = str(ai_data.get("summary", "")).strip()
    if not summary:
        summary = transcript_text[:300]

    # key_topics = clean_list(ai_data.get("key_topics", []), 7)
    key_topics = clean_list(ai_data.get("key_topics", []), 7)

    # SAFE ACTION ITEMS
    action_items = []
    raw_items = ai_data.get("action_items", [])

    if isinstance(raw_items, list):
        for item in raw_items:
            if isinstance(item, dict):
                action_items.append({
                    "owner": item.get("owner"),
                    "task": str(item.get("task", "")).strip(),
                    "priority": item.get("priority", "medium")
                })

    if not key_topics:
        key_topics = ["General discussion"]
        # 🔥 APPLY NAME MAPPING TO SPEAKERS
    for s in speakers:
        original = s["speaker"]
        if original in speaker_map:
            s["speaker"] = speaker_map[original]
        # ── FINAL REPORT ──────────────────────────
    report = {
    "meta": {
        "audio_filename": audio_filename,
        "duration_seconds": audio_duration,
        "word_count": word_count,
        "language": language,
        "generated_at": datetime.now().isoformat(),
        "transcript_id": transcript_id
    },

    "title": ai_data.get("title", "Meeting Report"),

    "participants": ai_data.get("participants", []),

    "summary": ai_data.get("summary", summary),

    "discussion_sections": ai_data.get("discussion_sections", []),

    "key_decisions": ai_data.get("key_decisions", []),

    "action_items": ai_data.get("action_items", []),

    "risks": ai_data.get("risks", []),

    "speakers": speakers if speakers else []
 }

    return report