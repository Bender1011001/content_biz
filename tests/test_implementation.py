"""
Test script to demonstrate the implemented features from next-steps-and-improvements.md.

This script tests:
1. Enhanced model selection
2. Content templates
3. A/B testing functionality
"""
import os
import json
import logging
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.database import get_db, engine
from app.db.models import Base, Brief, Content, Client
from app.services.ai_service import ModelSelector
from app.services.template_service import TemplateService
from app.services.ab_testing_service import ABTestingService
from app.services.crew_service import ContentCrewService
from app.services.quality_service import QualityService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a test database session
def get_test_db():
    """Create a fresh database session for testing."""
    # Connect to the database
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    return db

def create_test_client(db: Session):
    """Create a test client for the database."""
    client = Client(
        id=str(uuid.uuid4()),
        name="Test Client",
        email=f"test-{uuid.uuid4()}@example.com",
    )
    db.add(client)
    db.commit()
    return client

def create_test_brief(db: Session, client_id: str):
    """Create a test brief."""
    brief = Brief(
        id=str(uuid.uuid4()),
        client_id=client_id,
        brief_text="Create a blog post about AI content generation.",
        topic="AI Content Generation",
        tone="informative",
        target_audience="marketing professionals",
        word_count=500,
        content_type="blog",
        industry="tech",
        status="pending",
    )
    db.add(brief)
    db.commit()
    return brief

def test_model_selector():
    """Test the model selection logic."""
    logger.info("Testing model selection...")
    
    # Initialize the model selector
    selector = ModelSelector({})
    
    # Test selection for different content types and industries
    test_cases = [
        {"content_type": "blog", "industry": "tech", "length": 500, "budget_tier": "standard"},
        {"content_type": "whitepaper", "industry": "finance", "length": 2000, "budget_tier": "premium"},
        {"content_type": "social", "industry": "creative", "length": 100, "budget_tier": "economy"},
        {"content_type": "newsletter", "industry": "health", "length": 800, "budget_tier": "standard"},
    ]
    
    for case in test_cases:
        model = selector.select_model(
            content_type=case["content_type"],
            industry=case["industry"], 
            length=case["length"],
            budget_tier=case["budget_tier"]
        )
        logger.info(f"Selected model for {case['content_type']}/{case['industry']}: {model}")
    
    return True

def test_content_templates(db: Session):
    """Test the content template functionality."""
    logger.info("Testing content templates...")
    
    # Initialize the template service
    template_service = TemplateService(db)
    
    # Create a few templates
    templates = [
        {
            "name": "Tech Blog",
            "system_prompt": "You are a technology expert writing for a tech blog.",
            "user_prompt_template": "Write a {word_count}-word blog post about {topic} for {target_audience}. Use a {tone} tone.",
            "content_type": "blog",
            "industry": "tech",
            "description": "Template for technology blog posts",
        },
        {
            "name": "Finance Whitepaper",
            "system_prompt": "You are a financial expert writing detailed whitepapers.",
            "user_prompt_template": "Create a {word_count}-word whitepaper on {topic} targeting {target_audience}. Use a {tone} tone and include detailed analysis.",
            "content_type": "whitepaper",
            "industry": "finance",
            "description": "Template for finance whitepapers",
        },
    ]
    
    created_templates = []
    for template in templates:
        try:
            created = template_service.create_template(
                name=template["name"],
                system_prompt=template["system_prompt"],
                user_prompt_template=template["user_prompt_template"],
                content_type=template["content_type"],
                industry=template["industry"],
                description=template["description"],
            )
            created_templates.append(created)
            logger.info(f"Created template: {created.name}")
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
    
    # Test template rendering
    if created_templates:
        test_params = {
            "topic": "Artificial Intelligence",
            "word_count": 500,
            "target_audience": "tech enthusiasts",
            "tone": "informative",
        }
        
        rendered = template_service.render_template(created_templates[0].id, test_params)
        logger.info(f"Rendered template system prompt: {rendered['system_prompt'][:50]}...")
        logger.info(f"Rendered template user prompt: {rendered['user_prompt'][:50]}...")
    
    return created_templates

def test_ab_testing(db: Session):
    """Test the A/B testing functionality."""
    logger.info("Testing A/B testing...")
    
    # Create a client and brief
    client = create_test_client(db)
    brief = create_test_brief(db, client.id)
    
    # Initialize the A/B testing service
    ab_service = ABTestingService(db)
    
    # Create an A/B test with variants
    test = ab_service.create_test(
        name="Model Comparison Test",
        description="Testing different models for tech blog generation",
    )
    logger.info(f"Created A/B test: {test.id}")
    
    # Add variants
    variants = [
        {
            "name": "Claude Variant",
            "model": "anthropic/claude-3-sonnet-20240229",
            "weight": 1.0,
        },
        {
            "name": "Mistral Variant",
            "model": "mistralai/mistral-large-latest",
            "weight": 1.0,
        },
    ]
    
    created_variants = []
    for variant in variants:
        try:
            v = ab_service.add_variant(
                test_id=test.id,
                name=variant["name"],
                model=variant["model"],
                weight=variant["weight"],
            )
            created_variants.append(v)
            logger.info(f"Created variant: {v.name} using model {v.model}")
        except Exception as e:
            logger.error(f"Error creating variant: {str(e)}")
    
    # In a real scenario, we would run the test, but for this demo we'll just
    # simulate running it manually since we don't have actual API keys
    
    # Instead, create some mock content for demonstration
    for variant in created_variants:
        mock_content = Content(
            id=str(uuid.uuid4()),
            brief_id=brief.id,
            variant_id=variant.id,
            generated_text=f"This is mock content generated using the {variant.model} model.",
            model_used=variant.model,
            quality_score=85.0 if "claude" in variant.model.lower() else 80.0,
            delivery_status="ready_for_delivery",
            created_at=datetime.utcnow(),
        )
        db.add(mock_content)
    
    db.commit()
    
    # Get test results
    try:
        results = ab_service.get_test_results(test.id)
        logger.info(f"Test results: {json.dumps(results, indent=2, default=str)}")
        
        # End the test
        ab_service.end_test(test.id)
        logger.info(f"A/B test completed")
    except Exception as e:
        logger.error(f"Error getting test results: {str(e)}")
    
    return test

def main():
    """Run all tests."""
    # Connect to the database
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    
    try:
        logger.info("Starting implementation tests...")
        
        # Test model selection
        test_model_selector()
        
        # Test content templates
        templates = test_content_templates(db)
        
        # Test A/B testing
        test = test_ab_testing(db)
        
        logger.info("All tests completed successfully")
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
