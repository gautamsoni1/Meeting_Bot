from pydantic import BaseModel
from datetime import datetime


class UserToken(BaseModel):
    user_id: str
    created_at: datetime = datetime.utcnow()