import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Content
from ..schemas.content import ContentResponse
from ..services.delivery_service import DeliveryService

logger = logging.getLogger(__name__)
router = APIRouter()

# No client-facing endpoints remain in this router.
# Content retrieval and delivery are handled by the CrewAI workflow.
