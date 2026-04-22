# import json
# import os
# from datetime import datetime
# from apscheduler.schedulers.background import BackgroundScheduler
# import requests

# from config.config import NGROK_URL

# JOBS_FILE = "scheduled_jobs.json"
# RECORD_API = f"{NGROK_URL}/record"

# scheduler = BackgroundScheduler()


# # =========================
# # LOAD JOBS
# # =========================
# def _load_jobs():
#     if not os.path.exists(JOBS_FILE):
#         return {}

#     try:
#         with open(JOBS_FILE, "r") as f:
#             data = f.read().strip()

#             if not data:
#                 return {}

#             jobs = json.loads(data)

#             if isinstance(jobs, list):
#                 print("⚠️ Jobs file was list, resetting")
#                 return {}

#             return jobs

#     except Exception as e:
#         print("⚠️ Failed to load jobs:", e)
#         return {}


# # =========================
# # SAVE JOBS
# # =========================
# def _save_jobs(jobs):
#     try:
#         if not isinstance(jobs, dict):
#             print("⚠️ Invalid jobs format, resetting")
#             jobs = {}

#         with open(JOBS_FILE, "w") as f:
#             json.dump(jobs, f, indent=2)

#     except Exception as e:
#         print("❌ Failed to save jobs:", e)


# # =========================
# # ADD SCHEDULED MEETING
# # =========================
# def add_scheduled_meeting(job_id, meeting_url, scheduled_at_iso, user_id):
#     jobs = _load_jobs()

#     if not isinstance(jobs, dict):
#         jobs = {}

#     # ✅ PREVENT DUPLICATE JOB
#     if job_id in jobs:
#         print("⚠️ Job already exists, skipping")
#         return

#     jobs[job_id] = {
#         "meeting_url": meeting_url,
#         "scheduled_at": scheduled_at_iso,
#         "user_id": user_id,
#         "status": "pending"
#     }

#     _save_jobs(jobs)

#     print(f"📌 Job scheduled at {scheduled_at_iso}")


# # =========================
# # CHECK + FIRE JOBS
# # =========================
# def check_and_fire_jobs():
#     jobs = _load_jobs()

#     if not isinstance(jobs, dict):
#         print("⚠️ Invalid jobs format, resetting...")
#         jobs = {}
#         _save_jobs(jobs)
#         return

#     now = datetime.now()
#     changed = False

#     for job_id, job in jobs.items():

#         if not isinstance(job, dict):
#             continue

#         if job.get("status") != "pending":
#             continue

#         try:
#             scheduled = datetime.fromisoformat(job["scheduled_at"])
#         except Exception as e:
#             print(f"❌ Invalid time format for job {job_id}: {e}")
#             continue

#         print(f"\n⏳ Checking job: {job_id}")
#         print("🕒 NOW:", now)
#         print("🕒 SCHEDULED:", scheduled)

#         # =========================
#         # TIME MATCH
#         # =========================
#         if now >= scheduled:

#             print(f"🚀 Triggering job: {job_id}")

#             user_id = job.get("user_id")

#             if not user_id:
#                 print(f"❌ Missing user_id for job {job_id}")
#                 continue

#             try:
#                 res = requests.post(
#                     RECORD_API,
#                     json={
#                         "meeting_url": job["meeting_url"],
#                         "meeting_id": job_id,
#                         "user_id": user_id
#                     },
#                     timeout=10
#                 )

#                 print("📡 RECORD API STATUS:", res.status_code)

#                 job["status"] = "done"
#                 job["triggered_at"] = now.isoformat()
#                 changed = True

#                 print(f"✅ Recording started for job {job_id}")

#             except Exception as e:
#                 print(f"❌ Failed to call RECORD API: {e}")
#                 job["status"] = "error"
#                 changed = True

#     if changed:
#         _save_jobs(jobs)


# # =========================
# # START SCHEDULER
# # =========================
# def start_scheduler():
#     scheduler.add_job(check_and_fire_jobs, "interval", seconds=30)
#     scheduler.start()
#     print("⏰ Scheduler started (runs every 30 seconds)")











import json
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from config.config import NGROK_URL

RECORD_API = f"{NGROK_URL}/record"

scheduler = BackgroundScheduler()
JOBS_FILE = "scheduled_jobs.json"


def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return {}
    try:
        with open(JOBS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_jobs(jobs):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)


def add_scheduled_meeting(job_id, meeting_url, scheduled_at_iso, user_id):

    jobs = load_jobs()

    jobs[job_id] = {
        "meeting_url": meeting_url,
        "scheduled_at": scheduled_at_iso,
        "user_id": user_id,
        "status": "pending"
    }

    save_jobs(jobs)


def check_jobs():

    jobs = load_jobs()
    now = datetime.now()

    for job_id, job in jobs.items():

        if job["status"] != "pending":
            continue

        scheduled = datetime.fromisoformat(job["scheduled_at"])

        if now >= scheduled:

            requests.post(RECORD_API, json={
                "meeting_url": job["meeting_url"],
                "meeting_id": job_id,
                "user_id": job["user_id"]
            })

            job["status"] = "done"

    save_jobs(jobs)


def start_scheduler():
    scheduler.add_job(check_jobs, "interval", seconds=30)
    scheduler.start()
    print("⏰ Scheduler running")