from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PaymentBase(BaseModel):
    amount: float = 75.00
    
class PaymentCreate(PaymentBase):
    client_id: str
    brief_id: str
    payment_intent_id: str

class PaymentResponse(BaseModel):
    status: str
    brief_id: Optional[str] = None

class PaymentInDB(PaymentBase):
    id: str
    client_id: str
    brief_id: str
    status: str
    stripe_payment_id: str
    created_at: datetime

    class Config:
        orm_mode = True
