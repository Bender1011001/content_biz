import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import Base
from main import app

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the get_db dependency for testing
app.dependency_overrides[get_db] = override_get_db

# Create a test client
client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_submit_brief():
    """Test the brief submission endpoint"""
    # Mock Stripe payment service
    import unittest.mock as mock
    from app.services.payment_service import PaymentService
    
    # Create a mock for the Stripe payment intent and customer creation
    with mock.patch.object(PaymentService, 'get_or_create_customer') as mock_customer:
        mock_customer.return_value = "cus_mock123"
        
        with mock.patch.object(PaymentService, 'create_payment_intent') as mock_payment:
            # Set up the mock payment intent
            class MockPaymentIntent:
                def __init__(self):
                    self.client_secret = "pi_mock_secret123"
            
            mock_payment.return_value = MockPaymentIntent()
            
            # Test data for brief submission
            brief_data = {
                "client_name": "Test Client",
                "client_email": "test@example.com",
                "brief_text": "This is a test brief for content about AI technology.",
                "topic": "AI Technology",
                "tone": "professional",
                "target_audience": "Tech professionals",
                "word_count": 800
            }
            
            # Submit the brief
            response = client.post("/api/briefs/", json=brief_data)
            
            # Check the response
            assert response.status_code == 200
            data = response.json()
            assert "brief_id" in data
            assert "payment_intent_client_secret" in data
            assert data["payment_intent_client_secret"] == "pi_mock_secret123"

def test_get_admin_dashboard():
    """Test the admin dashboard endpoint"""
    response = client.get("/api/admin/clients")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
