from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class BriefBase(BaseModel):
    brief_text: str
    topic: Optional[str] = None
    tone: Optional[str] = None
    target_audience: Optional[str] = None
    word_count: Optional[int] = None

class BriefCreate(BriefBase):
    client_name: str
    client_email: EmailStr

class BriefResponse(BaseModel):
    brief_id: str
    payment_intent_client_secret: str

class BriefInDB(BriefBase):
    id: str
    client_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
