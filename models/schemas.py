from pydantic import BaseModel
# Image Summary Response
class UploadResponse(BaseModel):
    filename: str
    summary: str

# Optional: ChatRequest / ChatResponse
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    question: str
    answer: str

class ResponseModel(BaseModel):
    filename: str
    transcript: str
    summary: str
    word_count: int
    timestamp: str

class JoinMeetingRequest(BaseModel):
    meeting_url: str

