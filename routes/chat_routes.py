# from fastapi import APIRouter
# from pydantic import BaseModel

# from services.meeting_service import handle_meeting
# from services.pdf_qa_service import ask_pdf, create_vector_db
# from services.email_service import send_report_to_participants

# from db.mongo import chat_collection, report_collection
# from state.chat_state import set_state, get_state

# import os

# router = APIRouter()


# class ChatRequest(BaseModel):
#     user_id: str
#     message: str


# @router.post("/chat")
# def chat(req: ChatRequest):

#     user_id = req.user_id
#     message = req.message.strip()
#     msg_lower = message.lower()

#     # =========================
#     # SAVE USER MESSAGE
#     # =========================
#     chat_collection.insert_one({
#         "user_id": user_id,
#         "role": "user",
#         "message": message
#     })

#     state = get_state(user_id)

#     # =========================
#     # 📄 REPORT LOAD
#     # =========================
#     if "report" in msg_lower or "pdf" in msg_lower:

#         last_report = report_collection.find_one(
#             {"user_id": user_id},
#             sort=[("created_at", -1)]
#         )

#         if last_report and last_report.get("pdf_report_path"):

#             pdf_path = last_report["pdf_report_path"]

#             create_vector_db(user_id, pdf_path)

#             set_state(user_id, {
#                 "step": "pdf_qa",
#                 "pdf_path": pdf_path,
#                 "meeting_id": last_report.get("meeting_id")
#             })

#             filename = os.path.basename(pdf_path)
#             pdf_url = f"https://stimulatingly-glumpier-hannelore.ngrok-free.dev/reports/{filename}"

#             return {
#                 "message": "📄 Report loaded. Ask questions or type 'send report'.",
#                 "pdf_url": pdf_url
#             }

#     # =========================
#     # 📧 SEND REPORT TO PARTICIPANTS
#     # =========================
#     if "send report" in msg_lower:

#         meeting_id = None

#         if state:
#             meeting_id = state.get("meeting_id")

#         if not meeting_id:
#             return {"message": "❌ Meeting not found for sending report"}

#         result = send_report_to_participants(user_id, meeting_id)

#         return {"message": result}

#     # =========================
#     # 🧠 PDF Q&A MODE
#     # =========================
#     if state and state.get("step") == "pdf_qa":
#         response = ask_pdf(user_id, message)

#         chat_collection.insert_one({
#             "user_id": user_id,
#             "role": "bot",
#             "message": response
#         })

#         return {"message": response}

#     # =========================
#     # 📅 MEETING FLOW
#     # =========================
#     response = handle_meeting(user_id, message)

#     final_response = response.get("message", str(response))

#     chat_collection.insert_one({
#         "user_id": user_id,
#         "role": "bot",
#         "message": final_response
#     })

#     return {"message": final_response}






from fastapi import APIRouter
from pydantic import BaseModel

from services.meeting_service import handle_meeting
from services.pdf_qa_service import ask_pdf, create_vector_db
from services.email_service import send_report_to_participants

from db.mongo import chat_collection, report_collection
from state.chat_state import set_state, get_state

import os

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str
    message: str


# @router.post("/chat")
# def chat(req: ChatRequest):

#     user_id = req.user_id
#     message = req.message.strip()
#     msg_lower = message.lower()
    

#     # =========================
#     # ✅ SAVE USER MESSAGE (UPDATED)
#     # =========================
#     chat_collection.update_one(
#         {"user_id": user_id},
#         {
#             "$push": {
#                 "messages": {
#                     "role": "user",
#                     "message": message
#                 }
#             }
#         },
#         upsert=True
#     )

#     state = get_state(user_id)
#      # =========================
#     # 👋 GREETING HANDLER (NEW)
#     # =========================
#     greetings = ["hi", "hello", "hey", "hii", "helo", "good morning", "good evening"]

#     if any(greet in msg_lower for greet in greetings):

#         bot_reply = "👋 Hello! I can help you schedule meetings, view reports, or answer questions. What would you like to do?"

#         chat_collection.update_one(
#             {"user_id": user_id},
#             {
#                 "$push": {
#                     "messages": {
#                         "role": "bot",
#                         "message": bot_reply
#                     }
#                 }
#             }
#         )

#         return {"message": bot_reply}

#     # =========================
#     # 📄 REPORT LOAD
#     # =========================
#     if "report" in msg_lower or "pdf" in msg_lower:

#         last_report = report_collection.find_one(
#             {"user_id": user_id},
#             sort=[("created_at", -1)]
#         )

#         if last_report and last_report.get("pdf_report_path"):

#             pdf_path = last_report["pdf_report_path"]

#             create_vector_db(user_id, pdf_path)

#             set_state(user_id, {
#                 "step": "pdf_qa",
#                 "pdf_path": pdf_path,
#                 "meeting_id": last_report.get("meeting_id")
#             })

#             filename = os.path.basename(pdf_path)
#             pdf_url = f"https://stimulatingly-glumpier-hannelore.ngrok-free.dev/reports/{filename}"

#             bot_reply = "📄 Report loaded. Ask questions or type 'send report'."

#             # ✅ SAVE BOT MESSAGE
#             chat_collection.update_one(
#                 {"user_id": user_id},
#                 {
#                     "$push": {
#                         "messages": {
#                             "role": "bot",
#                             "message": bot_reply
#                         }
#                     }
#                 }
#             )

#             return {
#                 "message": bot_reply,
#                 "pdf_url": pdf_url
#             }

#     # =========================
#     # 📧 SEND REPORT
#     # =========================
#     if "send report" in msg_lower:

#         meeting_id = None

#         if state:
#             meeting_id = state.get("meeting_id")

#         if not meeting_id:
#             bot_reply = "❌ Meeting not found for sending report"

#             chat_collection.update_one(
#                 {"user_id": user_id},
#                 {
#                     "$push": {
#                         "messages": {
#                             "role": "bot",
#                             "message": bot_reply
#                         }
#                     }
#                 }
#             )

#             return {"message": bot_reply}

#         result = send_report_to_participants(user_id, meeting_id)

#         # ✅ SAVE BOT MESSAGE
#         chat_collection.update_one(
#             {"user_id": user_id},
#             {
#                 "$push": {
#                     "messages": {
#                         "role": "bot",
#                         "message": result
#                     }
#                 }
#             }
#         )

#         return {"message": result}

#     # =========================
#     # 🧠 PDF Q&A MODE
#     # =========================
#     if state and state.get("step") == "pdf_qa":

#         response = ask_pdf(user_id, message)

#         # ✅ SAVE BOT MESSAGE
#         chat_collection.update_one(
#             {"user_id": user_id},
#             {
#                 "$push": {
#                     "messages": {
#                         "role": "bot",
#                         "message": response
#                     }
#                 }
#             }
#         )

#         return {"message": response}
    
#     if "history" in msg_lower or "old chat" in msg_lower or "previous" in msg_lower:

#     chat_doc = chat_collection.find_one({"user_id": user_id})

#     if not chat_doc or "messages" not in chat_doc:
#         return {"message": "📭 No chat history found"}

#     messages = chat_doc["messages"][-10:]  # last 10 messages

#     history_text = "\n".join(
#         [f"{m['role']}: {m['message']}" for m in messages]
#     )

#     bot_reply = f"🧾 Your recent chat history:\n\n{history_text}"

#     chat_collection.update_one(
#         {"user_id": user_id},
#         {
#             "$push": {
#                 "messages": {
#                     "role": "bot",
#                     "message": bot_reply
#                 }
#             }
#         }
#     )

#     return {"message": bot_reply}

#     # =========================
#     # 📅 MEETING FLOW
#     # =========================
#     response = handle_meeting(user_id, message)

#     final_response = response.get("message", str(response))

#     # ✅ SAVE BOT MESSAGE
#     chat_collection.update_one(
#         {"user_id": user_id},
#         {
#             "$push": {
#                 "messages": {
#                     "role": "bot",
#                     "message": final_response
#                 }
#             }
#         }
#     )

#     return {"message": final_response}



@router.post("/chat")
def chat(req: ChatRequest):

    user_id = req.user_id
    message = req.message.strip()
    msg_lower = message.lower()

    # =========================
    # SAVE USER MESSAGE
    # =========================
    chat_collection.update_one(
        {"user_id": user_id},
        {
            "$push": {
                "messages": {
                    "role": "user",
                    "message": message
                }
            }
        },
        upsert=True
    )

    state = get_state(user_id)

    # ======================================================
    # 📜 HISTORY (HIGHEST PRIORITY)
    # ======================================================
    if "history" in msg_lower or "old chat" in msg_lower or "previous" in msg_lower:

        chat_doc = chat_collection.find_one({"user_id": user_id})

        if not chat_doc or "messages" not in chat_doc:
            bot_reply = "📭 No chat history found"

        else:
            messages = chat_doc["messages"][-10:]

            history_text = "\n".join(
                [f"{m['role']}: {m['message']}" for m in messages]
            )

            bot_reply = f"🧾 Your recent chat history:\n\n{history_text}"

        chat_collection.update_one(
            {"user_id": user_id},
            {"$push": {"messages": {"role": "bot", "message": bot_reply}}}
        )

        return {"message": bot_reply}

    # ======================================================
    # 👋 GREETING
    # ======================================================
    greetings = ["hi", "hello", "hey", "hii", "good morning", "good evening"]

    if any(g in msg_lower for g in greetings):

        bot_reply = "👋 Hello! I can help you schedule meetings, view reports, or answer questions."

        chat_collection.update_one(
            {"user_id": user_id},
            {"$push": {"messages": {"role": "bot", "message": bot_reply}}}
        )

        return {"message": bot_reply}

    # ======================================================
    # 📄 REPORT LOAD
    # ======================================================
    if "report" in msg_lower or "pdf" in msg_lower:

        last_report = report_collection.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )

        if last_report and last_report.get("pdf_report_path"):

            pdf_path = last_report["pdf_report_path"]

            create_vector_db(user_id, pdf_path)

            set_state(user_id, {
                "step": "pdf_qa",
                "pdf_path": pdf_path,
                "meeting_id": last_report.get("meeting_id")
            })

            filename = os.path.basename(pdf_path)
            pdf_url = f"https://stimulatingly-glumpier-hannelore.ngrok-free.dev/reports/{filename}"

            bot_reply = "📄 Report loaded. Ask questions or type 'send report'."

        else:
            bot_reply = "📭 No report found"

        chat_collection.update_one(
            {"user_id": user_id},
            {"$push": {"messages": {"role": "bot", "message": bot_reply}}}
        )

        return {"message": bot_reply, "pdf_url": pdf_url if 'pdf_url' in locals() else None}

    # ======================================================
    # 📧 SEND REPORT
    # ======================================================
    if "send report" in msg_lower:

        meeting_id = state.get("meeting_id") if state else None

        if not meeting_id:
            bot_reply = "❌ Meeting not found"

        else:
            bot_reply = send_report_to_participants(user_id, meeting_id)

        chat_collection.update_one(
            {"user_id": user_id},
            {"$push": {"messages": {"role": "bot", "message": bot_reply}}}
        )

        return {"message": bot_reply}

    # ======================================================
    # 🧠 PDF Q&A
    # ======================================================
    if state and state.get("step") == "pdf_qa":

        response = ask_pdf(user_id, message)

        chat_collection.update_one(
            {"user_id": user_id},
            {"$push": {"messages": {"role": "bot", "message": response}}}
        )

        return {"message": response}

    # ======================================================
    # 🤖 BOT JOIN CONFIRMATION
    # ======================================================
    if state and state.get("step") == "meeting_bot_confirm":

        meeting_link = state.get("meeting_link")
        meeting_id = state.get("meeting_id")

        if msg_lower in ["yes", "y"]:

            bot_reply = "🤖 Bot is joining meeting and recording started..."

            set_state(user_id, {
                "step": "meeting_running",
                "meeting_id": meeting_id
            })

        else:

            bot_reply = "👍 Okay, bot will NOT join. Meeting created only."

            set_state(user_id, {
                "step": "meeting_completed",
                "meeting_id": meeting_id
            })

        chat_collection.update_one(
            {"user_id": user_id},
            {"$push": {"messages": {"role": "bot", "message": bot_reply}}}
        )

        return {"message": bot_reply}

    # ======================================================
    # 📅 MEETING FLOW
    # ======================================================
    response = handle_meeting(user_id, message)

    final_response = response.get("message", str(response))

    meeting_link = response.get("meeting_url")
    meeting_id = response.get("meeting_id")

    if meeting_link:

        set_state(user_id, {
            "step": "meeting_bot_confirm",
            "meeting_id": meeting_id,
            "meeting_link": meeting_link
        })

        final_response = (
            f"📅 Meeting created 👉 {meeting_link}\n\n"
            f"🤖 Bot join & record? (yes/no)"
        )

    chat_collection.update_one(
        {"user_id": user_id},
        {"$push": {"messages": {"role": "bot", "message": final_response}}}
    )

    return {"message": final_response}