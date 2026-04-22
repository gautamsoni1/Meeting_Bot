from groq import Groq
from config.config import GROQ_API_KEY
from services.groq_client import build_chat_context
from datetime import datetime, timedelta, timezone
import json, re

client = Groq(api_key=GROQ_API_KEY)


# =========================
# SAFE JSON EXTRACTOR
# =========================
def safe_json_extract(text):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print("❌ JSON Parse Error:", e)
    return None


# =========================
# FIXED TIME EXTRACTOR
# =========================
def extract_time_from_text(text):
    # Normalize AM/PM spacing
    text = text.upper().replace("PM", " PM").replace("AM", " AM")

    match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)?', text)

    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        ampm = match.group(3)

        # Convert only if AM/PM exists
        if ampm:
            if hour <= 12:
                if ampm == "PM" and hour != 12:
                    hour += 12
                if ampm == "AM" and hour == 12:
                    hour = 0

        # Safety correction
        if hour > 23:
            hour = hour % 24

        return f"{hour:02d}:{minute:02d}"

    return None


# =========================
# MAIN PARSER
# =========================
def parse_meeting(user_id, text: str):

    history = build_chat_context(user_id)

    messages = [{
        "role": "system",
        "content": """
Return ONLY JSON:
{
  "title": "",
  "date": "",
  "time": "",
  "relative": "",
  "duration": 30
}
"""
    }]

    messages.extend(history)
    messages.append({"role": "user", "content": text})

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )

    raw = res.choices[0].message.content
    print("🧠 LLM RAW:", raw)

    data = safe_json_extract(raw)

    if not data:
        return None

    # ✅ Use timezone-safe current time
    now = datetime.now(timezone.utc).astimezone()
    text_lower = text.lower()

    # =========================
    # FORCE DATE (USER PRIORITY)
    # =========================
    if "today" in text_lower:
        data["date"] = now.strftime("%Y-%m-%d")

    elif "tomorrow" in text_lower:
        data["date"] = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    # =========================
    # FIX WRONG YEAR (🔥)
    # =========================
    try:
        if data.get("date"):
            year = int(data["date"].split("-")[0])
            current_year = now.year

            if year < current_year:
                data["date"] = data["date"].replace(str(year), str(current_year))
    except Exception as e:
        print("❌ Year fix error:", e)

    # =========================
    # FORCE TIME (HIGHEST PRIORITY)
    # =========================
    user_time = extract_time_from_text(text)
    if user_time:
        data["time"] = user_time

    # =========================
    # HANDLE "NOW"
    # =========================
    if "now" in text_lower:
        data["date"] = now.strftime("%Y-%m-%d")
        data["time"] = now.strftime("%H:%M")
        print("✅ FINAL PARSED DATA:", data)
        return data

    # =========================
    # APPLY RELATIVE (ONLY IF NO USER TIME)
    # =========================
    if data.get("relative") and not user_time:

        rel = data["relative"].lower()
        temp = now

        try:
            if "min" in rel:
                n = int(re.findall(r"\d+", rel)[0])
                temp += timedelta(minutes=n)

            elif "hour" in rel:
                n = int(re.findall(r"\d+", rel)[0])
                temp += timedelta(hours=n)

            elif "day" in rel:
                n = int(re.findall(r"\d+", rel)[0])
                temp += timedelta(days=n)

            elif "tomorrow" in rel:
                temp += timedelta(days=1)

            data["date"] = temp.strftime("%Y-%m-%d")
            data["time"] = temp.strftime("%H:%M")

        except Exception as e:
            print("❌ Relative parsing error:", e)

    # =========================
    # DEFAULT TIME
    # =========================
    if not data.get("time"):
        data["time"] = "10:00"

    # =========================
    # PREVENT PAST TIME (🔥 CRITICAL FIX)
    # =========================
    try:
        meeting_dt = datetime.strptime(
            f"{data['date']} {data['time']}",
            "%Y-%m-%d %H:%M"
        )

        if meeting_dt < now.replace(tzinfo=None):
            print("⚠️ Past time detected → shifting to next valid time")

            meeting_dt = now + timedelta(minutes=2)

            data["date"] = meeting_dt.strftime("%Y-%m-%d")
            data["time"] = meeting_dt.strftime("%H:%M")

    except Exception as e:
        print("❌ Time validation error:", e)

    print("✅ FINAL PARSED DATA:", data)

    return data