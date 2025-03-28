# app/api/templates.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.templates import (
    ContentTemplate,
    ContentTemplateCreate,
    ContentTemplateUpdate,
    RenderedTemplate,
    TemplateParams,
)
from app.services.template_service import TemplateService
from app.services.auth_service import get_admin_user, get_current_user

# Main router - original functionality remains accessible
router = APIRouter()

# Create separate routers for admin and client endpoints
admin_router = APIRouter(tags=["admin", "templates"])
client_router = APIRouter(tags=["templates"])

# Import for template analytics
import json
from sqlalchemy import func
from app.db.models import Content
# app/api/templates.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.templates import (
    ContentTemplate,
    ContentTemplateCreate,
    ContentTemplateUpdate,
    RenderedTemplate,
    TemplateParams,
)
from app.services.template_service import TemplateService
from app.services.auth_service import get_admin_user, get_current_user

# Main router - original functionality remains accessible
router = APIRouter()

# Create separate routers for admin and client endpoints

# Admin endpoints
@admin_router.post("/", response_model=ContentTemplate, status_code=status.HTTP_201_CREATED)
def admin_create_template(
    template: ContentTemplateCreate, db: Session = Depends(get_db), _=Depends(get_admin_user)
):
    """Create a new content template (admin only)."""
    template_service = TemplateService(db)
    try:
        return template_service.create_template(
            name=template.name,
            system_prompt=template.system_prompt,
            user_prompt_template=template.user_prompt_template,
            content_type=template.content_type,
            description=template.description,
            industry=template.industry,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create template: {str(e)}",
        )

@admin_router.get("/", response_model=List[ContentTemplate])
def admin_list_templates(
    content_type: Optional[str] = None,
    industry: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_admin_user)
):
    """List all content templates with optional filtering (admin only)."""
    template_service = TemplateService(db)
    return template_service.list_templates(content_type=content_type, industry=industry)

@admin_router.put("/{template_id}", response_model=ContentTemplate)
def admin_update_template(
    template_id: str, 
    template: ContentTemplateUpdate, 
    db: Session = Depends(get_db),
    _=Depends(get_admin_user)
):
    """Update a content template (admin only)."""
    template_service = TemplateService(db)
    updated_template = template_service.update_template(
        template_id, template.dict(exclude_unset=True)
    )
    if not updated_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found",
        )
    return updated_template

@admin_router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_template(
    template_id: str, 
    db: Session = Depends(get_db),
    _=Depends(get_admin_user)
):
    """Delete a content template (admin only)."""
    template_service = TemplateService(db)
    result = template_service.delete_template(template_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found",
        )
    return None

@admin_router.get("/analytics", response_model=dict)
def get_template_analytics(db: Session = Depends(get_db), _=Depends(get_admin_user)):
    """Get analytics on template usage (admin only)."""
    # Count content generated using templates
    templated_content_count = db.query(Content).filter(
        Content.generation_metadata.isnot(None),
        Content.generation_metadata.contains('"template_id"')
    ).count()
    
    # Count total content
    total_content_count = db.query(Content).count()
    
    # Get template usage by template ID
    template_usage = []
    contents_with_templates = db.query(Content).filter(
        Content.generation_metadata.isnot(None),
        Content.generation_metadata.contains('"template_id"')
    ).all()
    
    template_counts = {}
    for content in contents_with_templates:
        try:
            metadata = json.loads(content.generation_metadata)
            if "template_id" in metadata and metadata["template_id"]:
                template_id = metadata["template_id"]
                template_name = metadata.get("template_name", "Unknown")
                key = f"{template_id}:{template_name}"
                template_counts[key] = template_counts.get(key, 0) + 1
        except (json.JSONDecodeError, AttributeError):
            pass
    
    for template_key, count in template_counts.items():
        template_id, template_name = template_key.split(":", 1)
        template_usage.append({
            "template_id": template_id,
            "template_name": template_name,
            "usage_count": count,
            "percentage": (count / total_content_count * 100) if total_content_count > 0 else 0
        })
    
    # Sort by usage count, descending
    template_usage.sort(key=lambda x: x["usage_count"], reverse=True)
    
    # Get average quality score for templated vs non-templated content
    templated_avg_quality = db.query(func.avg(Content.quality_score)).filter(
        Content.generation_metadata.isnot(None),
        Content.generation_metadata.contains('"template_id"'),
        Content.quality_score.isnot(None)
    ).scalar() or 0
    
    non_templated_avg_quality = db.query(func.avg(Content.quality_score)).filter(
        (Content.generation_metadata.is_(None) | 
         ~Content.generation_metadata.contains('"template_id"')),
        Content.quality_score.isnot(None)
    ).scalar() or 0
    
    return {
        "total_content_count": total_content_count,
        "templated_content_count": templated_content_count,
        "template_adoption_rate": (templated_content_count / total_content_count * 100) if total_content_count > 0 else 0,
        "templated_avg_quality": float(templated_avg_quality),
        "non_templated_avg_quality": float(non_templated_avg_quality),
        "quality_improvement": float(templated_avg_quality - non_templated_avg_quality),
        "template_usage": template_usage
    }

# Client-facing endpoints
@client_router.get("/", response_model=List[ContentTemplate])
def get_available_templates(
    content_type: Optional[str] = None,
    industry: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Get templates available to the user with optional filtering."""
    template_service = TemplateService(db)
    return template_service.list_templates(content_type=content_type, industry=industry)

@client_router.get("/{template_id}", response_model=ContentTemplate)
def get_client_template(
    template_id: str, 
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Get a content template by ID (client endpoint)."""
    template_service = TemplateService(db)
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found",
        )
    return template

@client_router.get("/best/{content_type}", response_model=ContentTemplate)
def get_client_best_template(
    content_type: str, 
    industry: Optional[str] = None, 
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Get the best template for a content type and optional industry (client endpoint)."""
    template_service = TemplateService(db)
    template = template_service.get_best_template(content_type, industry)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No template found for content type '{content_type}'",
        )
    return template


@router.post("/", response_model=ContentTemplate, status_code=status.HTTP_201_CREATED)
def create_template(
    template: ContentTemplateCreate, db: Session = Depends(get_db)
):
    """Create a new content template."""
    template_service = TemplateService(db)
    try:
        return template_service.create_template(
            name=template.name,
            system_prompt=template.system_prompt,
            user_prompt_template=template.user_prompt_template,
            content_type=template.content_type,
            description=template.description,
            industry=template.industry,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create template: {str(e)}",
        )


@router.get("/", response_model=List[ContentTemplate])
def list_templates(
    content_type: Optional[str] = None,
    industry: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List content templates with optional filtering."""
    template_service = TemplateService(db)
    return template_service.list_templates(content_type=content_type, industry=industry)


@router.get("/{template_id}", response_model=ContentTemplate)
def get_template(template_id: str, db: Session = Depends(get_db)):
    """Get a content template by ID."""
    template_service = TemplateService(db)
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found",
        )
    return template


@router.get("/by-name/{name}", response_model=ContentTemplate)
def get_template_by_name(name: str, db: Session = Depends(get_db)):
    """Get a content template by name."""
    template_service = TemplateService(db)
    template = template_service.get_template_by_name(name)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with name '{name}' not found",
        )
    return template


@router.put("/{template_id}", response_model=ContentTemplate)
def update_template(
    template_id: str, template: ContentTemplateUpdate, db: Session = Depends(get_db)
):
    """Update a content template."""
    template_service = TemplateService(db)
    updated_template = template_service.update_template(
        template_id, template.dict(exclude_unset=True)
    )
    if not updated_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found",
        )
    return updated_template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: str, db: Session = Depends(get_db)):
    """Delete a content template."""
    template_service = TemplateService(db)
    result = template_service.delete_template(template_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found",
        )
    return None


@router.post("/{template_id}/render", response_model=RenderedTemplate)
def render_template(
    template_id: str, params: TemplateParams, db: Session = Depends(get_db)
):
    """Render a content template with parameters."""
    template_service = TemplateService(db)
    try:
        return template_service.render_template(template_id, params.params)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not render template: {str(e)}",
        )


@router.post("/by-name/{name}/render", response_model=RenderedTemplate)
def render_template_by_name(
    name: str, params: TemplateParams, db: Session = Depends(get_db)
):
    """Render a content template by name with parameters."""
    template_service = TemplateService(db)
    try:
        return template_service.render_template_by_name(name, params.params)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not render template: {str(e)}",
        )


@router.get("/best/{content_type}", response_model=ContentTemplate)
def get_best_template(
    content_type: str, industry: Optional[str] = None, db: Session = Depends(get_db)
):
    """Get the best template for a content type and optional industry."""
    template_service = TemplateService(db)
    template = template_service.get_best_template(content_type, industry)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No template found for content type '{content_type}'",
        )
    return template
