"""
Simplified test for template integration in content generation.
"""
import unittest
from unittest.mock import patch, MagicMock

from app.services.template_service import TemplateService
from app.db.models import ContentTemplate


class TestTemplateFeatures(unittest.TestCase):
    """Test template features directly without running the full content generation."""
    
    def test_template_service_fill_template(self):
        """Test the fill_template method of TemplateService."""
        # Create a test template
        template = ContentTemplate(
            id="test-id",
            name="Test Template",
            system_prompt="You are a {industry} expert",
            user_prompt_template="Write about {topic} for {target_audience} in {tone} tone. Word count: {word_count}",
            content_type="blog",
            industry="tech"
        )
        
        # Test brief data
        brief = {
            "topic": "AI Applications",
            "tone": "professional",
            "target_audience": "executives",
            "word_count": 500,
            "brief_text": "Focus on business applications",
            "industry": "technology",
            "content_type": "whitepaper"
        }
        
        # Create service instance
        service = TemplateService()
        
        # Call the method
        result = service.fill_template(template, brief)
        
        # Verify results
        self.assertEqual(result["system_prompt"], "You are a {industry} expert")
        self.assertEqual(
            result["user_prompt"], 
            "Write about AI Applications for executives in professional tone. Word count: 500"
        )
        
        # Test with missing parameters
        brief_minimal = {
            "topic": "AI"
        }
        
        result = service.fill_template(template, brief_minimal)
        self.assertTrue("AI" in result["user_prompt"])
        self.assertTrue("general audience" in result["user_prompt"])
        self.assertTrue("professional" in result["user_prompt"])


if __name__ == "__main__":
    unittest.main()
