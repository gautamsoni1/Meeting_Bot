# 🤖 Meeting Recorder Bot

Record any Zoom / Google Meet / Microsoft Teams meeting and get a downloadable MP3 link via ngrok.

---

## 📁 Project Structure

```
meeting_bot/
├── .env                          # Your secrets
├── main.py                       # FastAPI app entry point
├── requirements.txt
├── recordings/                   # Downloaded MP3s are saved here
└── app/
    ├── config.py                 # Loads .env
    ├── routes/
    │   ├── bot_routes.py         # /join-meeting, /status, /recording
    │   └── webhook_routes.py     # /webhook  (Recall.ai callback)
    ├── services/
    │   ├── recall_client.py      # All Recall API calls
    │   ├── webhook_handler.py    # Processes recording.done event
    │   └── downloader.py        # Streams MP3 to disk
    └── utils/
        └── Store.py              # In-memory bot status Store
```

---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Edit .env
```dotenv
RECALL_API_KEY=your_key_here
RECALL_REGION=us-west-2
BASE_URL=https://us-west-2.recall.ai/api/v1
NGROK_URL=https://YOUR-NGROK-URL.ngrok-free.app
```

### 3. Start ngrok (in a separate terminal)
```bash
ngrok http 8000
```
Copy the HTTPS URL and paste it as `NGROK_URL` in your `.env`.

### 4. Start the server
```bash
uvicorn main:app --reload --port 8000
```

---

## 🔄 Full Flow

```
1. POST /join-meeting  →  Bot joins the meeting
2. Meeting runs...     →  Bot records audio
3. Meeting ends        →  Recall sends webhook to /webhook
4. App downloads MP3   →  Saved to /recordings/{bot_id}.mp3
5. GET /recording/{bot_id}  →  Returns public download link
6. Click the link      →  Download your MP3 via ngrok
```

---

## 📬 API Endpoints

### `POST /join-meeting`
Send bot to a meeting.

**Request:**
```json
{ "meeting_url": "https://meet.google.com/xxx-yyyy-zzz" }
```

**Response:**
```json
{
  "message": "✅ Bot is joining the meeting",
  "bot_id": "abc123",
  "status_url": "/status/abc123",
  "recording_url": "/recording/abc123"
}
```

---

### `GET /status/{bot_id}`
Poll to check recording status.

**Response (while recording):**
```json
{ "bot_id": "abc123", "status": "recording", "public_url": null }
```

**Response (when done):**
```json
{ "bot_id": "abc123", "status": "done", "public_url": "https://your-ngrok.ngrok-free.app/download/abc123.mp3" }
```

---

### `GET /recording/{bot_id}`
Get the download link once ready.

**Response:**
```json
{
  "bot_id": "abc123",
  "status": "done",
  "message": "✅ Recording ready!",
  "download_url": "https://your-ngrok.ngrok-free.app/download/abc123.mp3"
}
```

---

### `POST /webhook`
Automatically called by Recall.ai when meeting ends. Do not call manually.

---

## 🐛 Bugs Fixed (vs original code)

| File | Bug | Fix |
|------|-----|-----|
| `bot_routes.py` | `webhook_handler` imported but never called | Moved to `webhook_routes.py` properly |
| `webhook_routes.py` | `request.json()` called twice → crash | Read body once |
| `webhook_routes.py` | `handle_webhook_event` never called | Added call |
| `webhook_handler.py` | Wrong event `recording.completed` | Correct: `bot.status_change` + `status.code == done` |
| `webhook_handler.py` | Wrong data path for recording URL | Use `get_bot()` then `/audio_mixed` API |
| `bot_service.py` | `recording_config: {audio: True}` is invalid | Correct: `audio_mixed_mp3: {}` |
| `downloader.py` | Loads entire file into RAM | Streaming download with `iter_content` |
| `db.py` | Never implemented | Replaced with `utils/Store.py` |
| `main.py` | No static file serving | Added `StaticFiles` at `/download` |