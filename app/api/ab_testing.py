# app/api/ab_testing.py
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
from app.db.database import get_db
from app.services.ab_testing_service import ABTestingService
# Assuming auth_service exists and provides get_admin_user based on plan discussion
from app.services.auth_service import get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ab-testing"])

class Variant(BaseModel):
    model: Optional[str] = None
    template_id: Optional[str] = None

class ABTestCreate(BaseModel):
    brief_id: str
    variants: List[Variant]

# Define ABTestResult based on get_test_results output in the service
class ABTestResult(BaseModel):
    test_id: str
    brief_id: str
    status: str
    variants: List[Dict] # Should match the structure from get_test_results
    winner_index: Optional[int]
    metrics: Dict
    created_at: Optional[str] # Use Optional[str] for isoformat
    completed_at: Optional[str] # Use Optional[str] for isoformat

@router.post("/admin/ab-tests", response_model=dict)
async def create_ab_test(test: ABTestCreate, db: Session = Depends(get_db), _ = Depends(get_admin_user)):
    """Create a new A/B test (admin only)."""
    service = ABTestingService(db)
    try:
        # Pass variants as list of dicts, excluding unset values if needed
        test_id = await service.create_test(test.brief_id, [v.dict(exclude_unset=True) for v in test.variants])
        return {"test_id": test_id}
    except ValueError as e:
        # Specific error from service (e.g., < 2 variants)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch broader exceptions during test creation/variant running
        logger.error(f"API Error creating A/B test for brief {test.brief_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during A/B test creation.")


@router.post("/admin/ab-tests/{test_id}/select-winner", response_model=dict)
async def select_winner(test_id: str, winner_index: int, metrics: Dict = {},
                      db: Session = Depends(get_db), _ = Depends(get_admin_user)):
    """Select the winning variant (admin only)."""
    service = ABTestingService(db)
    try:
        success = await service.select_winner(test_id, winner_index, metrics)
        if not success:
            # Service might return False if test already completed
             raise HTTPException(status_code=409, detail=f"Failed to select winner for test {test_id}. It might be already completed or the index is invalid.")
        return {"status": "success"}
    except ValueError as e:
        # Handle specific errors like test not found or invalid index
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"API Error selecting winner for test {test_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during winner selection.")


@router.get("/admin/ab-test-results/{test_id}", response_model=ABTestResult)
async def get_test_results(test_id: str, db: Session = Depends(get_db), _ = Depends(get_admin_user)):
    """Get A/B test results (admin only)."""
    service = ABTestingService(db)
    try:
        results = await service.get_test_results(test_id)
        # Service raises ValueError if test not found, so no need for explicit check here
        return results
    except ValueError as e:
        # Test not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"API Error getting results for test {test_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error retrieving test results.")
