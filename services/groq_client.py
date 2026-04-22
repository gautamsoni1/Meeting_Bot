from groq import Groq
from config.config import GROQ_API_KEY
from db.mongo import chat_collection

client = Groq(api_key=GROQ_API_KEY)


# ✅ Get last messages from DB
def get_last_messages(user_id, limit=10):
    chats = chat_collection.find(
        {"user_id": user_id}
    ).sort("_id", -1).limit(limit)

    return list(chats)


# ✅ Convert DB chats → LLM format
def build_chat_context(user_id):

    messages = []

    chats = get_last_messages(user_id)

    for chat in reversed(chats):

        role = chat.get("role", "user")

        # 🔥 FIX ROLE
        if role not in ["system", "user", "assistant"]:
            if role == "bot":
                role = "assistant"
            else:
                role = "user"

        messages.append({
            "role": role,
            "content": chat.get("message", "")
        })

    return messages


# ✅ MAIN CHAT FUNCTION
def chat_with_groq(user_id: str, message: str):

    # 🔹 Step 1: Load previous conversation
    history = build_chat_context(user_id)

    # 🔹 Step 2: Build messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

    # add previous chats
    messages.extend(history)

    # ✅ add current user message (FIXED)
    messages.append({
        "role": "user",
        "content": message
    })

    # 🔹 Step 3: Call Groq
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.5,
        max_tokens=300
    )

    reply = response.choices[0].message.content

    # 🔹 Step 4: Save conversation in DB
    chat_collection.insert_one({
        "user_id": user_id,
        "role": "user",
        "message": message
    })

    chat_collection.insert_one({
        "user_id": user_id,
        "role": "assistant",   # ✅ ALWAYS assistant
        "message": reply
    })

    return reply