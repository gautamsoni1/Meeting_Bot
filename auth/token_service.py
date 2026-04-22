from db.mongo import token_collection
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


# ✅ SAVE TOKEN
def save_token(user_id, token_data):

    expiry = datetime.utcnow() + timedelta(days=7)

    data = {
        "user_id": user_id,
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "client_id": token_data.get("client_id"),
        "client_secret": token_data.get("client_secret"),
        "expires_at": expiry
    }

    token_collection.update_one(
        {"user_id": user_id},
        {"$set": data},
        upsert=True
    )


# ✅ GET TOKEN (AUTO REFRESH)
def get_token(user_id):
    data = token_collection.find_one({"user_id": user_id})

    if not data:
        return None

    creds = Credentials(
        token=data.get("access_token"),
        refresh_token=data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret")
    )

    # 🔥 Auto refresh token
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

        token_collection.update_one(
            {"user_id": user_id},
            {"$set": {"access_token": creds.token}}
        )

    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "client_id": data.get("client_id"),
        "client_secret": data.get("client_secret")
    }