# app/schemas/templates.py
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ContentTemplateBase(BaseModel):
    """Base model for content templates."""
    name: str
    system_prompt: str
    user_prompt_template: str
    content_type: str
    description: Optional[str] = None
    industry: Optional[str] = None


class ContentTemplateCreate(ContentTemplateBase):
    """Schema for creating a content template."""
    pass


class ContentTemplateUpdate(BaseModel):
    """Schema for updating a content template."""
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    content_type: Optional[str] = None
    industry: Optional[str] = None


class ContentTemplate(ContentTemplateBase):
    """Schema for a content template."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateParams(BaseModel):
    """Schema for template parameters."""
    params: dict


class RenderedTemplate(BaseModel):
    """Schema for a rendered template."""
    system_prompt: str
    user_prompt: str
