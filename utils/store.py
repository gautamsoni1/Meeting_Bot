# """
# Simple in-memory Store

# Structure:
# bot_Store[bot_id] = {
#     "status": "recording" | "done" | "error",
#     "mp3_download_url": str | None,   # Recall CDN URL
#     "local_file": str | None,         # saved file path
#     "public_url": str | None,         # ngrok/public URL
# }
# """

# from typing import Dict, Optional

# # 🔥 Main storage
# bot_Store: Dict[str, Dict] = {}


# def upsert(bot_id: str, **kwargs) -> None:
#     """
#     Create or update bot entry safely
#     """

#     # ✅ Create default if not exists
#     # in upsert(), change the default block to:
#     if bot_id not in bot_Store:
#         bot_Store[bot_id] = {
#         "status":          "recording",
#         "mp3_download_url": None,
#         "local_file":      None,
#         "public_url":      None,
#         "report_status":   "pending",
#         "report_pdf_path": None,
#         "report_pdf_url":  None,
#     }

#     # ✅ Update only provided fields
#     bot_Store[bot_id].update(kwargs)


# def get(bot_id: str) -> Optional[Dict]:
#     """
#     Get bot info
#     """
#     return bot_Store.get(bot_id)


# def exists(bot_id: str) -> bool:
#     """
#     Check if bot exists
#     """
#     return bot_id in bot_Store


# def delete(bot_id: str) -> None:
#     """
#     Remove bot from store (optional cleanup)
#     """
#     if bot_id in bot_Store:
#         del bot_Store[bot_id]


# def reset() -> None:
#     """
#     Clear all store (useful for testing)
#     """
#     bot_Store.clear()



# utils/store.py
"""
Simple in-memory store for bot state.

Structure per bot:
  bot_Store[bot_id] = {
      "status"          : "recording" | "processing" | "done" | "error",
      "mp3_download_url": str | None,   # Recall CDN URL
      "local_file"      : str | None,   # absolute path to recordings/{bot_id}.mp3
      "public_url"      : str | None,   # {NGROK_URL}/download/{bot_id}.mp3
      "report_status"   : "pending" | "done" | "error",
      "report_pdf_path" : str | None,
      "report_pdf_url"  : str | None,
  }
"""

from typing import Dict, Optional

# 🔥 Main in-memory store
bot_Store: Dict[str, Dict] = {}


def upsert(bot_id: str, **kwargs) -> None:
    """Create or update a bot entry. Only provided fields are updated."""
    if bot_id not in bot_Store:
        bot_Store[bot_id] = {
            "status":           "recording",
            "mp3_download_url": None,
            "local_file":       None,
            "public_url":       None,
            "report_status":    "pending",
            "report_pdf_path":  None,
            "report_pdf_url":   None,
        }
    bot_Store[bot_id].update(kwargs)


def get(bot_id: str) -> Optional[Dict]:
    """Return bot info dict or None if not found."""
    return bot_Store.get(bot_id)


def exists(bot_id: str) -> bool:
    """Check if a bot entry exists."""
    return bot_id in bot_Store


def delete(bot_id: str) -> None:
    """Remove a bot entry from the store."""
    if bot_id in bot_Store:
        del bot_Store[bot_id]


def reset() -> None:
    """Clear the entire store (useful for testing)."""
    bot_Store.clear()