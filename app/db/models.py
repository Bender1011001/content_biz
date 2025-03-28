import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Client(Base):
    __tablename__ = 'clients'
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    briefs = relationship("Brief", back_populates="client")
    payments = relationship("Payment", back_populates="client")

class Brief(Base):
    __tablename__ = 'briefs'
    id = Column(String, primary_key=True, default=generate_uuid)
    client_id = Column(String, ForeignKey('clients.id'), nullable=False)
    brief_text = Column(Text, nullable=False)
    topic = Column(String, nullable=True)
    tone = Column(String, nullable=True)
    target_audience = Column(String, nullable=True)
    word_count = Column(Integer, nullable=True)
    status = Column(String, default="pending")
    industry = Column(String, nullable=True, default="general")
    content_type = Column(String, nullable=True, default="blog")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = relationship("Client", back_populates="briefs")
    content = relationship("Content", back_populates="brief", uselist=False)
    payment = relationship("Payment", back_populates="brief", uselist=False)

class Content(Base):
    __tablename__ = 'contents'
    id = Column(String, primary_key=True, default=generate_uuid)
    brief_id = Column(String, ForeignKey('briefs.id'), nullable=False)
    generated_text = Column(Text, nullable=True)
    quality_score = Column(Float, nullable=True)
    delivery_status = Column(String, default="pending")
    model_used = Column(String, nullable=True)
    generation_metadata = Column(Text, nullable=True)
    variant_id = Column(String, ForeignKey('ab_test_variants.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    feedback = Column(Text, nullable=True)
    
    brief = relationship("Brief", back_populates="content")
    variant = relationship("ABTestVariant", back_populates="contents")

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(String, primary_key=True, default=generate_uuid)
    client_id = Column(String, ForeignKey('clients.id'), nullable=False)
    brief_id = Column(String, ForeignKey('briefs.id'), nullable=False)
    amount = Column(Float, default=75.00)
    status = Column(String, default="pending")
    stripe_payment_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    client = relationship("Client", back_populates="payments")
    brief = relationship("Brief", back_populates="payment")

class ABTest(Base):
    __tablename__ = 'ab_tests'
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="active")
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    variants = relationship("ABTestVariant", back_populates="test")

class ABTestVariant(Base):
    __tablename__ = 'ab_test_variants'
    id = Column(String, primary_key=True, default=generate_uuid)
    test_id = Column(String, ForeignKey('ab_tests.id'), nullable=False)
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    prompt_template = Column(Text, nullable=True)
    parameters = Column(Text, nullable=True)  # JSON string of parameter overrides
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    test = relationship("ABTest", back_populates="variants")
    contents = relationship("Content", back_populates="variant")

class ContentTemplate(Base):
    __tablename__ = 'content_templates'
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    content_type = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
