from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ContentBase(BaseModel):
    generated_text: Optional[str] = None
    quality_score: Optional[float] = None
    delivery_status: str = "pending"

class ContentCreate(ContentBase):
    brief_id: str

class ContentResponse(ContentBase):
    id: str
    brief_id: str
    created_at: datetime

    class Config:
        orm_mode = True

class QualityCheckResult(BaseModel):
    content_id: str
    quality_score: float
    grammar_score: float
    coherence_score: float
    issues: Optional[List[str]] = None
    status: str
