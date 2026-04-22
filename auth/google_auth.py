import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config.config import SCOPES, GOOGLE_REDIRECT_URI
from auth.token_service import save_token
from db.mongo import user_collection

import uuid
from datetime import datetime

flow_store = {}


def create_flow():
    return Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )


# 🔹 LOGIN (NO user_id now)
def get_auth_url():
    flow = create_flow()

    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )

    flow_store[state] = {
        "flow": flow
    }

    print("LOGIN STATE:", state)

    return auth_url


# # 🔹 CALLBACK
def handle_callback(full_url: str, state: str):

    stored = flow_store.get(state)

    if not stored:
        return {"error": "❌ Invalid or expired state"}

    flow = stored["flow"]

    flow.fetch_token(authorization_response=full_url)

    creds = flow.credentials

    # =========================
    # ✅ GET USER EMAIL FROM GOOGLE
    # =========================
    service = build("oauth2", "v2", credentials=creds)
    user_info = service.userinfo().get().execute()

    email = user_info.get("email")

    print("📧 EMAIL FROM GOOGLE:", email)   # ✅ DEBUG

    # =========================
    # ✅ CHECK USER IN DB
    # =========================
    user = user_collection.find_one({"email": email})

    if user:
        user_id = user["user_id"]

        # 🔥 OPTIONAL FIX (if old user had no email)
        user_collection.update_one(
            {"user_id": user_id},
            {"$set": {"email": email}}
        )

        print("✅ EXISTING USER:", email)

    else:
        user_id = str(uuid.uuid4())

        # 🔥 THIS CREATES users COLLECTION
        user_collection.insert_one({
            "user_id": user_id,
            "email": email,
            "created_at": datetime.utcnow()
        })

        print("🆕 NEW USER CREATED:", email)

    # =========================
    # ✅ SAVE TOKEN WITH USER_ID + EMAIL
    # =========================
    token_data = {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "email": email   # 🔥 ADD THIS
    }

    # 🔥 PASS EMAIL ALSO
    save_token(user_id, token_data)

    # =========================
    # CLEANUP
    # =========================
    del flow_store[state]

    return {
        "message": "✅ Google Connected Successfully",
        "user_id": user_id,
        "email": email
    }