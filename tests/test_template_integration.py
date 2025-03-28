"""
Test for template integration in content generation.

This test verifies that templates are correctly integrated into the content
generation workflow.
"""
import os
import unittest
import uuid
import json
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.crew_service import ContentCrewService
from app.services.template_service import TemplateService
from app.db.models import ContentTemplate


class TestTemplateIntegration(unittest.TestCase):
    """Test template integration in content generation."""

    def setUp(self):
        """Set up test environment."""
        # Mock environment
        os.environ["OPENROUTER_API_KEY"] = "test_key"
        
        # Create a test template
        self.template_id = str(uuid.uuid4())
        self.template = ContentTemplate(
            id=self.template_id,
            name="Test Template",
            system_prompt="You are a test expert",
            user_prompt_template="Write about {topic} for {target_audience} in {tone} tone",
            content_type="test",
            industry="test"
        )
        
        # Mock brief data
        self.brief_data = {
            "topic": "Test Topic",
            "tone": "professional",
            "target_audience": "testers",
            "word_count": 100,
            "brief_text": "This is a test",
            "industry": "tech",
            "content_type": "blog"
        }

    @patch('app.services.template_service.TemplateService.get_template')
    @patch('app.services.crew_service.ContentCrewService._select_model')
    @patch('openai.OpenAI')
    def test_template_integration(self, mock_openai_class, mock_select_model, mock_get_template):
        """Test that templates are correctly integrated into content generation."""
        # Configure mocks
        mock_get_template.return_value = self.template
        mock_select_model.return_value = "test-model"
        
        # Set up OpenAI mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_chat = MagicMock()
        mock_client.chat = mock_chat
        mock_completions = MagicMock()
        mock_chat.completions = mock_completions
        
        # Mock the create method and its response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Generated test content"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_completions.create.return_value = mock_response
        
        # Create service with mocked dependencies
        service = ContentCrewService(brief_data=self.brief_data)
        
        # Test without template (default prompts)
        with patch.object(service, '_save_to_database', return_value="content_id"):
            result = service.run_crew(save_to_db=False)
            self.assertEqual(result, "Generated test content")
            
            # Check model selection was called
            mock_select_model.assert_called_once()
            
            # Check OpenAI was called with default prompts
            args, kwargs = mock_client.chat.completions.create.call_args
            messages = kwargs.get('messages', [])
            self.assertEqual(len(messages), 2)  # system and user prompt
            
            # Reset mocks for next test
            mock_select_model.reset_mock()
            mock_client.chat.completions.create.reset_mock()
        
        # Test with template
        with patch.object(service, '_save_to_database', return_value="content_id"):
            result = service.run_crew(save_to_db=False, template_id=self.template_id)
            self.assertEqual(result, "Generated test content")
            
            # Check template retrieval was called
            mock_get_template.assert_called_with(self.template_id)
            
            # Check model selection was called
            mock_select_model.assert_called_once()
            
            # Check OpenAI was called with template prompts
            args, kwargs = mock_client.chat.completions.create.call_args
            messages = kwargs.get('messages', [])
            self.assertEqual(len(messages), 2)  # system and user prompt
            self.assertEqual(messages[0]['content'], "You are a test expert")
            
    @patch('app.services.template_service.TemplateService.get_template')
    @patch('app.services.crew_service.ContentCrewService._select_model')
    @patch('openai.OpenAI')
    def test_template_fallback(self, mock_openai_class, mock_select_model, mock_get_template):
        """Test fallback to default prompts when template is not found."""
        # Configure mocks
        mock_get_template.return_value = None  # Template not found
        mock_select_model.return_value = "test-model"
        
        # Set up OpenAI mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_chat = MagicMock()
        mock_client.chat = mock_chat
        mock_completions = MagicMock()
        mock_chat.completions = mock_completions
        
        # Mock the create method and its response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Generated test content"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_completions.create.return_value = mock_response
        
        # Create service with mocked dependencies
        service = ContentCrewService(brief_data=self.brief_data)
        
        # Test with invalid template ID
        with patch.object(service, '_save_to_database', return_value="content_id"):
            result = service.run_crew(save_to_db=False, template_id="invalid_id")
            self.assertEqual(result, "Generated test content")
            
            # Check OpenAI was called with default prompts
            args, kwargs = mock_client.chat.completions.create.call_args
            messages = kwargs.get('messages', [])
            self.assertEqual(len(messages), 2)  # system and user prompt
            # The default prompt system message will contain "professional content creator"
            self.assertIn("content creator", messages[0]['content'])

    @patch('app.services.template_service.TemplateService.get_template')
    @patch('app.services.crew_service.ContentCrewService._select_model')
    @patch('openai.OpenAI')
    @patch('app.services.crew_service.get_db')
    def test_template_metadata_storage(self, mock_get_db, mock_openai_class, mock_select_model, mock_get_template):
        """Test that template metadata is stored in the database."""
        # Configure mocks
        mock_get_template.return_value = self.template
        mock_select_model.return_value = "test-model"
        
        # Set up mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = iter([mock_session])
        
        # Set up OpenAI mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_chat = MagicMock()
        mock_client.chat = mock_chat
        mock_completions = MagicMock()
        mock_chat.completions = mock_completions
        
        # Mock the create method and its response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Generated test content"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_completions.create.return_value = mock_response
        
        # Create service with mocked dependencies
        service = ContentCrewService(brief_data=self.brief_data, brief_id="test_brief_id")
        
        # Run with template
        result = service.run_crew(template_id=self.template_id)
        
        # Verify content was saved with template metadata
        mock_session.add.assert_called_once()
        content_obj = mock_session.add.call_args[0][0]
        self.assertEqual(content_obj.brief_id, "test_brief_id")
        self.assertEqual(content_obj.generated_text, "Generated test content")
        
        # Verify metadata contains template info
        import json
        metadata = json.loads(content_obj.generation_metadata)
        self.assertEqual(metadata["template_id"], self.template_id)
        self.assertEqual(metadata["template_name"], "Test Template")


if __name__ == "__main__":
    unittest.main()
