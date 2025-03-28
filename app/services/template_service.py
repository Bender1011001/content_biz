# app/services/template_service.py
import json
import logging
from typing import Dict, List, Optional, Union

from app.db.database import get_db
from app.db.models import ContentTemplate
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class TemplateService:
    """Service for managing content prompt templates."""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize the template service.
        
        Args:
            db: Optional database session
        """
        self.db = db
    
    def _get_db(self):
        """Get database session or use the provided one."""
        if self.db:
            return self.db
        return next(get_db())
    
    def create_template(self, 
                        name: str, 
                        system_prompt: str, 
                        user_prompt_template: str, 
                        content_type: str,
                        description: Optional[str] = None,
                        industry: Optional[str] = None) -> ContentTemplate:
        """Create a new content template.
        
        Args:
            name: Unique name for the template
            system_prompt: System prompt to use with this template
            user_prompt_template: User prompt template with placeholders
            content_type: Type of content (blog, whitepaper, etc.)
            description: Optional description of the template
            industry: Optional industry specialization
            
        Returns:
            The created ContentTemplate object
        """
        db = self._get_db()
        
        # Create template
        template = ContentTemplate(
            name=name,
            description=description,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            content_type=content_type,
            industry=industry
        )
        
        try:
            db.add(template)
            db.commit()
            db.refresh(template)
            logger.info(f"Template '{name}' created successfully")
            return template
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create template: {str(e)}")
            raise
    
    def get_template(self, template_id: str) -> Optional[ContentTemplate]:
        """Get a template by ID.
        
        Args:
            template_id: The template ID
            
        Returns:
            The ContentTemplate object or None if not found
        """
        db = self._get_db()
        return db.query(ContentTemplate).filter(ContentTemplate.id == template_id).first()
    
    def get_template_by_name(self, name: str) -> Optional[ContentTemplate]:
        """Get a template by name.
        
        Args:
            name: The template name
            
        Returns:
            The ContentTemplate object or None if not found
        """
        db = self._get_db()
        return db.query(ContentTemplate).filter(ContentTemplate.name == name).first()
    
    def list_templates(self, 
                       content_type: Optional[str] = None, 
                       industry: Optional[str] = None) -> List[ContentTemplate]:
        """List templates with optional filtering.
        
        Args:
            content_type: Optional content type filter
            industry: Optional industry filter
            
        Returns:
            List of ContentTemplate objects
        """
        db = self._get_db()
        query = db.query(ContentTemplate)
        
        if content_type:
            query = query.filter(ContentTemplate.content_type == content_type)
        
        if industry:
            query = query.filter(ContentTemplate.industry == industry)
        
        return query.all()
    
    def update_template(self, 
                        template_id: str, 
                        updates: Dict) -> Optional[ContentTemplate]:
        """Update a template.
        
        Args:
            template_id: The template ID
            updates: Dictionary of fields to update
            
        Returns:
            The updated ContentTemplate or None if not found
        """
        db = self._get_db()
        template = db.query(ContentTemplate).filter(ContentTemplate.id == template_id).first()
        
        if not template:
            logger.warning(f"Template with ID {template_id} not found")
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        try:
            db.commit()
            db.refresh(template)
            logger.info(f"Template '{template.name}' updated successfully")
            return template
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update template: {str(e)}")
            raise
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template.
        
        Args:
            template_id: The template ID
            
        Returns:
            True if deleted, False if not found
        """
        db = self._get_db()
        template = db.query(ContentTemplate).filter(ContentTemplate.id == template_id).first()
        
        if not template:
            logger.warning(f"Template with ID {template_id} not found")
            return False
        
        try:
            db.delete(template)
            db.commit()
            logger.info(f"Template '{template.name}' deleted successfully")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete template: {str(e)}")
            raise
    
    def render_template(self, template_id: str, params: Dict) -> Dict[str, str]:
        """Render a template with provided parameters.
        
        Args:
            template_id: The template ID
            params: Dictionary of parameters to substitute in the template
            
        Returns:
            Dictionary with rendered system_prompt and user_prompt
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")
        
        return self._render_template_object(template, params)
    
    def render_template_by_name(self, name: str, params: Dict) -> Dict[str, str]:
        """Render a template by name with provided parameters.
        
        Args:
            name: The template name
            params: Dictionary of parameters to substitute in the template
            
        Returns:
            Dictionary with rendered system_prompt and user_prompt
        """
        template = self.get_template_by_name(name)
        if not template:
            raise ValueError(f"Template with name '{name}' not found")
        
        return self._render_template_object(template, params)
    
    def _render_template_object(self, template: ContentTemplate, params: Dict) -> Dict[str, str]:
        """Render a template object with provided parameters.
        
        Args:
            template: The ContentTemplate object
            params: Dictionary of parameters to substitute in the template
            
        Returns:
            Dictionary with rendered system_prompt and user_prompt
        """
        # System prompt isn't typically templated, but we'll support simple string replacements
        system_prompt = template.system_prompt
        
        # For user prompt, allow string formatting with the provided parameters
        try:
            user_prompt = template.user_prompt_template.format(**params)
        except KeyError as e:
            # Log missing keys and attempt a partial rendering
            logger.warning(f"Missing template parameter: {str(e)}")
            # Replace only the parameters we have
            user_prompt = template.user_prompt_template
            for key, value in params.items():
                placeholder = '{' + key + '}'
                user_prompt = user_prompt.replace(placeholder, str(value))
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
    
    def fill_template(self, template: ContentTemplate, brief: Dict) -> Dict[str, str]:
        """Fill a template with brief data.
        
        This is a convenience method specifically for use with content briefs.
        
        Args:
            template: The ContentTemplate object
            brief: Dictionary containing brief data
            
        Returns:
            Dictionary with rendered system_prompt and user_prompt
        """
        # Extract standard brief parameters
        params = {
            "topic": brief.get("topic", "unspecified topic"),
            "tone": brief.get("tone", "professional"),
            "target_audience": brief.get("target_audience", "general audience"),
            "word_count": brief.get("word_count", 500),
            "brief_text": brief.get("brief_text", ""),
            "industry": brief.get("industry", "general"),
            "content_type": brief.get("content_type", "blog")
        }
        
        # Include any additional parameters from the brief
        for key, value in brief.items():
            if key not in params:
                params[key] = value
                
        return self._render_template_object(template, params)
    
    def get_best_template(self, content_type: str, industry: Optional[str] = None) -> Optional[ContentTemplate]:
        """Get the best template for a given content type and industry.
        
        Args:
            content_type: The content type
            industry: Optional industry specialization
            
        Returns:
            The best matching ContentTemplate or None if none found
        """
        db = self._get_db()
        query = db.query(ContentTemplate).filter(ContentTemplate.content_type == content_type)
        
        if industry:
            # First try to find an exact industry match
            industry_match = query.filter(ContentTemplate.industry == industry).first()
            if industry_match:
                return industry_match
        
        # Otherwise, return a generic template for this content type
        return query.filter(ContentTemplate.industry.is_(None)).first()
