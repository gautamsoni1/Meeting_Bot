from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
from groq import Groq

vector_store = {}
chat_memory = {}

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def create_vector_db(user_id, pdf_path):

    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    embeddings = HuggingFaceEmbeddings()
    db = FAISS.from_documents(docs, embeddings)

    vector_store[user_id] = db
    chat_memory[user_id] = []


def ask_pdf(user_id, question):

    db = vector_store.get(user_id)

    if not db:
        return "Report session expired. Please open report again."

    docs = db.similarity_search(question, k=5)

    context = "\n\n".join(list(dict.fromkeys([d.page_content for d in docs])))

    prompt = f"""
You are a strict meeting report assistant.

RULES:
- Use ONLY context
- If not found say "Not found in report"

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a strict assistant"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        answer = response.choices[0].message.content

    except Exception as e:
        return f"Groq error: {str(e)}"

    chat_memory[user_id].append({"role": "user", "content": question})
    chat_memory[user_id].append({"role": "assistant", "content": answer})

    return answer