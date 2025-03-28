import os
import logging
import uuid
import json
import time  # Added import
from datetime import datetime
from typing import Dict, Optional, Tuple

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from app.services.ai_service import ModelSelector
from app.services.template_service import TemplateService
from app.db.database import get_db
from app.db.models import Brief, Content, ContentTemplate

logger = logging.getLogger(__name__)

class ContentCrewService:
    """
    Service to orchestrate content creation using AI.
    
    Leverages specialized model selection based on content requirements.
    """
    
    def __init__(self, brief_data=None, brief_id=None, api_key=None, config=None):
        """
        Initialize the content creation service.
        
        Args:
            brief_data: Dictionary containing brief information
            brief_id: ID of an existing brief in the database
            api_key: OpenRouter API key (optional)
            config: Configuration dictionary (optional)
        """
        self.brief_data = brief_data
        self.brief_id = brief_id
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.config = config or {}
        self.model_selector = ModelSelector(self.config)
        self.template_service = TemplateService()
        
        # Initialize OpenAI client with OpenRouter base URL
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def run_crew(self, save_to_db=True, force_model: Optional[str] = None, template_id: Optional[str] = None):
        """
        Generate content based on the brief.
        
        Features automatic retries (up to 3 attempts with 2 second delay) for transient failures.
        
        Args:
            save_to_db: Whether to save the generated content to database
            force_model: Optional model to use, overriding automatic selection
            template_id: Optional template ID to use for prompt generation
            
        Returns:
            String (content ID if save_to_db=True, otherwise generated content)
        """
        try:
            brief = self._get_brief_data()
            model = force_model or self._select_model(brief)
            
            # Use template if specified, otherwise fall back to default prompts
            if template_id:
                template = self.template_service.get_template(template_id)
                if not template:
                    logger.warning(f"Template {template_id} not found, using default prompts")
                    system_prompt, user_prompt = self._create_prompts(brief)
                else:
                    logger.info(f"Using template '{template.name}' (ID: {template_id})")
                    rendered = self.template_service.render_template(template_id, brief)
                    system_prompt = rendered["system_prompt"]
                    user_prompt = rendered["user_prompt"]
            else:
                system_prompt, user_prompt = self._create_prompts(brief)
            
            logger.info(f"Generating content for topic: {brief.get('topic')} with model: {model}")

            start_time = time.time() # Track generation time

            # Generate content using OpenRouter
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=self._calculate_tokens(brief.get('word_count', 500)),
            )

            generation_time = time.time() - start_time # Calculate generation time

            # Extract the generated content
            generated_content = response.choices[0].message.content
            
            if save_to_db and self.brief_id:
                content_id = self._save_to_database(generated_content, model, template_id, generation_time) # Pass generation_time
                logger.info(f"Content saved with ID: {content_id}")
                return content_id
            return generated_content
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            return self._generate_error_content(brief, str(e))
            
    def _get_brief_data(self) -> Dict:
        """Retrieve brief data from either passed dictionary or database"""
        if self.brief_data:
            return self.brief_data
        if self.brief_id:
            db = next(get_db())
            brief = db.query(Brief).filter(Brief.id == self.brief_id).first()
            if brief:
                return {
                    'topic': brief.topic,
                    'tone': brief.tone,
                    'target_audience': brief.target_audience,
                    'word_count': brief.word_count,
                    'brief_text': brief.brief_text,
                    'industry': getattr(brief, 'industry', 'general'),
                    'content_type': getattr(brief, 'content_type', 'blog')
                }
        raise ValueError("No brief data provided")
    
    def _select_model(self, brief: Dict) -> str:
        """Select the most appropriate model based on content parameters"""
        return self.model_selector.select_model(
            content_type=brief.get('content_type', 'blog'),
            industry=brief.get('industry', 'general'),
            length=brief.get('word_count', 500),
            budget_tier=brief.get('budget_tier', 'standard')
        )
    
    def _create_prompts(self, brief: Dict) -> tuple[str, str]:
        """Create system and user prompts based on brief information"""
        topic = brief.get('topic', '')
        tone = brief.get('tone', 'professional')
        target_audience = brief.get('target_audience', 'general audience')
        word_count = brief.get('word_count', 500)
        brief_text = brief.get('brief_text', '')
        industry = brief.get('industry', 'general')
        content_type = brief.get('content_type', 'blog')
        
        system_prompt = self._get_system_prompt(content_type, industry)
        user_prompt = f"""
Write a {word_count}-word {content_type} about {topic} for {target_audience}.
Use a {tone} tone. Additional brief info: {brief_text}.
Ensure the content is structured with headings and paragraphs, engaging, and readable.
Target approximately {word_count} words.
"""
        return system_prompt, user_prompt
    
    def _get_system_prompt(self, content_type: str, industry: str) -> str:
        """Generate specialized system prompt based on content type and industry"""
        base_prompt = "You are a professional content creator specializing in high-quality content."
        content_type_prompts = {
            "blog": "You excel at writing engaging blog posts with valuable insights.",
            "whitepaper": "You specialize in authoritative whitepapers with researched data.",
            "social": "You craft compelling social media content that drives engagement.",
            "newsletter": "You create informative newsletters that retain readers.",
            "technical": "You produce clear, accurate technical content."
        }
        industry_prompts = {
            "tech": "You have expertise in technology trends and innovations.",
            "finance": "You understand financial markets and strategies.",
            "health": "You communicate health info accurately and ethically.",
            "creative": "You produce inspiring, artistic content.",
            "legal": "You explain legal concepts clearly and accurately."
        }
        prompt_parts = [base_prompt]
        if content_type.lower() in content_type_prompts:
            prompt_parts.append(content_type_prompts[content_type.lower()])
        if industry.lower() in industry_prompts:
            prompt_parts.append(industry_prompts[industry.lower()])
        return " ".join(prompt_parts)
        
    def _calculate_tokens(self, word_count: int) -> int:
        """Calculate appropriate token count for generation based on word count"""
        return int(word_count * 3)  # Buffer for response

    def _save_to_database(self, content_text: str, model_used: str, 
                         template_id: Optional[str] = None, generation_time: float = None) -> str: # Added generation_time parameter
        """Save generated content to the database"""
        db = next(get_db())

        # Prepare metadata with template information if available
        metadata = None
        if template_id:
            template = self.template_service.get_template(template_id)
            metadata = {
                "template_id": template_id,
                "template_name": template.name if template else "Unknown"
            }
        
        content = Content(
            id=str(uuid.uuid4()),
            brief_id=self.brief_id,
            generated_text=content_text,
            delivery_status="pending",
            model_used=model_used,
            generation_metadata=json.dumps(metadata) if metadata else None,
            generation_time=generation_time,  # Save generation_time
            needs_review=True,  # Set needs_review flag
            created_at=datetime.utcnow()
        )
        db.add(content)
        db.commit()
        return content.id
    
    def _generate_error_content(self, brief: Optional[Dict], error_msg: str) -> str:
        """Generate placeholder content in case of errors"""
        topic = brief.get('topic', 'Unknown Topic') if brief else 'Unknown Topic'
        return f"# Error: {topic}\n\nPlaceholder content due to error: {error_msg}"
