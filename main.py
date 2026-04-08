from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes.meeting_routes import router as meeting_router
from routes import bot_routes, webhook_routes
from config.config import RECORDINGS_DIR, NGROK_URL

from dotenv import load_dotenv
import os

# ==============================
# 🔹 LOAD ENV
# ==============================
load_dotenv()

# ==============================
# 🔹 APP
# ==============================
app = FastAPI(
    title="Image-to-Text + Meeting Recorder API",
    version="1.0.0",
)

# ==============================
# 🔹 STATIC FILES
# ==============================

# 👉 recordings (mp3)
app.mount("/download", StaticFiles(directory=RECORDINGS_DIR), name="recordings")

# 👉 reports (docx) ✅ IMPORTANT
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

app.include_router(meeting_router)

# ---- Bot ----
app.include_router(bot_routes.router)
app.include_router(webhook_routes.router)

# ==============================
# 🔹 ROOT
# ==============================
@app.get("/")
def root():
    return {
        "message": "🚀 Combined API running",
        "ngrok_url": NGROK_URL,
        "download_examples": {
            "mp3": f"{NGROK_URL}/download/sample.mp3",
            "docx": f"{NGROK_URL}/reports/sample.docx"
        }
    }
