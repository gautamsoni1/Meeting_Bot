import json
import time
from pathlib import Path

SESSION_FILE = Path("session.json")

SESSION_TTL = 7 * 24 * 60 * 60  # 7 days


def save_session(user_id):
    data = {
        "user_id": user_id,
        "created_at": time.time()
    }
    SESSION_FILE.write_text(json.dumps(data))


def get_session():
    if not SESSION_FILE.exists():
        return None

    data = json.loads(SESSION_FILE.read_text())

    if time.time() - data["created_at"] > SESSION_TTL:
        return None

    return data["user_id"]