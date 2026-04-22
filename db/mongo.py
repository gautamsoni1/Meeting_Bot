from pymongo import MongoClient
from config.config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["meeting_ai"]

user_collection = db["users"] 
token_collection = db["tokens"]
meeting_collection = db["meetings"]
chat_collection = db["chats"]
report_collection = db["reports"]