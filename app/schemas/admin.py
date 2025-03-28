from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ClientList(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime

    class Config:
        orm_mode = True

class BriefDetail(BaseModel):
    id: str
    client_id: str
    brief_text: str
    topic: Optional[str] = None
    tone: Optional[str] = None
    target_audience: Optional[str] = None
    word_count: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ContentDetail(BaseModel):
    id: str
    brief_id: str
    generated_text: Optional[str] = None
    quality_score: Optional[float] = None
    delivery_status: str
    created_at: datetime
    feedback: Optional[str] = None

    class Config:
        orm_mode = True

class PaymentList(BaseModel):
    id: str
    client_id: str
    brief_id: str
    amount: float
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
