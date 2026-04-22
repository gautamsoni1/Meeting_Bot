import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from db.mongo import report_collection, meeting_collection


# =========================
# EMAIL CONFIG
# =========================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")


# =========================
# GET PARTICIPANTS (FIXED)
# =========================
def get_participants(user_id, meeting_id):

    # 1st try meeting collection
    meeting = meeting_collection.find_one({
        "user_id": user_id,
        "event_id": meeting_id
    })

    participants = []

    if meeting:
        participants = meeting.get("participants", [])

    # fallback → report collection
    if not participants:
        report = report_collection.find_one({
            "user_id": user_id,
            "meeting_id": meeting_id
        })

        if report:
            participants = report.get("participants", [])

    # clean emails
    emails = []
    for p in participants:
        if isinstance(p, str):
            emails.append(p)
        elif isinstance(p, dict):
            email = p.get("email")
            if email:
                emails.append(email)

    return list(set(emails))  # remove duplicates


# =========================
# SEND SINGLE EMAIL
# =========================
def send_email(to_email, subject, body, attachment_path=None):

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        raise Exception("Email credentials missing")

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    # attachment
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(attachment_path)}"
        )
        msg.attach(part)

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()


# =========================
# SEND REPORT TO ALL PARTICIPANTS
# =========================
def send_report_to_participants(user_id, meeting_id):

    report = report_collection.find_one({
        "user_id": user_id,
        "meeting_id": meeting_id
    })

    if not report:
        return "❌ Report not found"

    pdf_path = report.get("pdf_report_path")

    if not pdf_path or not os.path.exists(pdf_path):
        return "❌ PDF not available"

    participants = get_participants(user_id, meeting_id)

    if not participants:
        return "⚠️ No participants found"

    sent = 0

    for email in participants:

        if not email:
            continue

        try:
            send_email(
                to_email=email,
                subject="📄 Meeting Report",
                body="Please find your meeting report attached.",
                attachment_path=pdf_path
            )
            sent += 1

        except Exception as e:
            print(f"❌ Failed email {email}: {e}")

    return f"✅ Report sent to {sent} participants"