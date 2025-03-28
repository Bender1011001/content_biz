# app/services/ab_testing_service.py
import uuid
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import ABTest, ABTestVariant, Content
from app.services.crew_service import ContentCrewService

logger = logging.getLogger(__name__)

class ABTestingService:
    """Manage A/B testing for content generation."""

    def __init__(self, db: Session = None, config=None):
        self.db = db or next(get_db())
        self.config = config or {}
        # Initialize ContentCrewService; config might be needed depending on its __init__
        self.content_service = ContentCrewService(config=config)

    async def create_test(self, brief_id: str, variants: List[Dict]) -> str:
        """Create an A/B test with specified variants."""
        if not variants or len(variants) < 2:
            raise ValueError("At least 2 variants required for A/B test")

        test_id = str(uuid.uuid4())
        # Assuming ABTest model has these fields based on markdown context
        test = ABTest(
            id=test_id,
            brief_id=brief_id,
            status="in_progress",
            variants_json=json.dumps(variants), # Storing variant definitions
            created_at=datetime.utcnow()
            # winner_index, metrics_json, completed_at are set later
        )
        self.db.add(test)
        self.db.commit() # Commit test creation first

        variant_contents = []
        try:
            for i, variant in enumerate(variants):
                # Ensure brief_id is set for the service instance if needed
                self.content_service.brief_id = brief_id
                # NOTE: If run_crew is not async, this await will cause issues.
                # Assuming run_crew is sync based on current file content.
                # If run_crew becomes async, add 'await' here.
                content_id = self.content_service.run_crew(
                    save_to_db=True,
                    force_model=variant.get("model"),
                    template_id=variant.get("template_id")
                )
                # Assuming ABTestVariant model has these fields
                variant_result = ABTestVariant(
                    id=str(uuid.uuid4()),
                    test_id=test_id,
                    variant_index=i, # Store the index (0, 1, ...)
                    content_id=content_id,
                    created_at=datetime.utcnow()
                )
                self.db.add(variant_result)
                variant_contents.append(content_id)

            self.db.commit() # Commit all variant results together
            logger.info(f"A/B test {test_id} created with {len(variants)} variants, content IDs: {variant_contents}")
            return test_id
        except Exception as e:
            logger.error(f"Error during variant generation for test {test_id}: {e}")
            # Consider rollback or cleanup logic here if needed
            self.db.rollback()
            raise # Re-raise the exception after logging

    async def select_winner(self, test_id: str, winner_index: int, metrics: Dict = None) -> bool:
        """Mark the winning variant based on metrics."""
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            logger.error(f"Attempted to select winner for non-existent test {test_id}")
            raise ValueError(f"Test {test_id} not found")
        if test.status == "completed":
             logger.warning(f"Test {test_id} is already completed. Cannot re-select winner.")
             return False # Or raise error?

        # Validate winner_index
        num_variants = len(json.loads(test.variants_json))
        if not (0 <= winner_index < num_variants):
             logger.error(f"Invalid winner_index {winner_index} for test {test_id} with {num_variants} variants.")
             raise ValueError(f"Invalid winner_index: {winner_index}")

        test.status = "completed"
        test.winner_index = winner_index
        test.metrics_json = json.dumps(metrics) if metrics else None
        test.completed_at = datetime.utcnow()
        try:
            self.db.commit()
            logger.info(f"A/B test {test_id} completed, winner: variant {winner_index}")
            return True
        except Exception as e:
            logger.error(f"Failed to commit winner selection for test {test_id}: {e}")
            self.db.rollback()
            raise

    async def get_test_results(self, test_id: str) -> Dict:
        """Retrieve detailed results of an A/B test."""
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            logger.error(f"Attempted to get results for non-existent test {test_id}")
            raise ValueError(f"Test {test_id} not found")

        # Get associated variants and their content
        variants_query = self.db.query(ABTestVariant, Content)\
            .join(Content, ABTestVariant.content_id == Content.id)\
            .filter(ABTestVariant.test_id == test_id)\
            .order_by(ABTestVariant.variant_index)\
            .all()

        variant_data = []
        for variant_record, content_record in variants_query:
            # Ensure content_record has the required fields after migration
            variant_data.append({
                "variant_index": variant_record.variant_index,
                "content_id": content_record.id,
                "model_used": content_record.model_used,
                # Safely parse generation_metadata
                "template_id": json.loads(content_record.generation_metadata or '{}').get("template_id"),
                "generation_time": content_record.generation_time,
                "needs_review": content_record.needs_review,
                "is_winner": variant_record.variant_index == test.winner_index if test.winner_index is not None else None
            })

        return {
            "test_id": test.id,
            "brief_id": test.brief_id,
            "status": test.status,
            "variants": variant_data, # List of detailed variant results
            "winner_index": test.winner_index,
            "metrics": json.loads(test.metrics_json) if test.metrics_json else {},
            "created_at": test.created_at.isoformat() if test.created_at else None,
            "completed_at": test.completed_at.isoformat() if test.completed_at else None
        }
