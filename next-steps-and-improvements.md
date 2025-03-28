Sprint 3: A/B Testing Framework (Weeks 5-7, Q2 2025)
Objectives
Fully implement app/services/ab_testing_service.py to create, manage, and analyze A/B tests comparing model and template combinations.
Extend crew_service.py to support A/B test variants with force_model and template_id.
Add API endpoints for A/B test management (/admin/ab-tests, /admin/ab-test-results).
Integrate basic quality metrics (e.g., generation time, manual review flags) into test results.
Target: Reduce manual review rate to <15% by identifying optimal generation strategies.
Timeline
Week 5: Implement ab_testing_service.py, update crew_service.py.
Week 6: Add API endpoints, extend database with quality metrics.
Week 7: Test integration, analyze initial A/B test results.
Tasks
Implement app/services/ab_testing_service.py
Build a service to create A/B tests, generate variant content, and select winners based on metrics.
Modify app/services/crew_service.py
Enhance run_crew to support A/B test variants and log generation metadata.
Extend app/db/models.py
Add quality metrics fields to Content and refine ABTest relationships.
Add API Endpoints in app/api/ab_testing.py
Provide admin endpoints for test creation and result analysis.
Test and Validate
Run A/B tests with sample briefs, verify functionality and quality improvements.
Code Implementation
1. app/services/ab_testing_service.py
python

Collapse

Wrap

Copy
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
        self.content_service = ContentCrewService(config=config)

    async def create_test(self, brief_id: str, variants: List[Dict]) -> str:
        """Create an A/B test with specified variants."""
        if not variants or len(variants) < 2:
            raise ValueError("At least 2 variants required for A/B test")
        
        test_id = str(uuid.uuid4())
        test = ABTest(
            id=test_id,
            brief_id=brief_id,
            status="in_progress",
            variants_json=json.dumps(variants),
            created_at=datetime.utcnow()
        )
        self.db.add(test)
        self.db.commit()

        variant_contents = []
        for i, variant in enumerate(variants):
            self.content_service.brief_id = brief_id
            content_id = self.content_service.run_crew(
                save_to_db=True,
                force_model=variant.get("model"),
                template_id=variant.get("template_id")
            )
            variant_result = ABTestVariant(
                id=str(uuid.uuid4()),
                test_id=test_id,
                variant_index=i,
                content_id=content_id,
                created_at=datetime.utcnow()
            )
            self.db.add(variant_result)
            variant_contents.append(content_id)
        
        self.db.commit()
        logger.info(f"A/B test {test_id} created with {len(variants)} variants")
        return test_id

    async def select_winner(self, test_id: str, winner_index: int, metrics: Dict = None) -> bool:
        """Mark the winning variant based on metrics."""
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        test.status = "completed"
        test.winner_index = winner_index
        test.metrics_json = json.dumps(metrics) if metrics else None
        test.completed_at = datetime.utcnow()
        self.db.commit()
        logger.info(f"A/B test {test_id} completed, winner: variant {winner_index}")
        return True

    async def get_test_results(self, test_id: str) -> Dict:
        """Retrieve detailed results of an A/B test."""
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        variants = self.db.query(ABTestVariant).filter(ABTestVariant.test_id == test_id).all()
        variant_data = []
        for variant in variants:
            content = self.db.query(Content).filter(Content.id == variant.content_id).first()
            variant_data.append({
                "variant_index": variant.variant_index,
                "content_id": content.id,
                "model_used": content.model_used,
                "template_id": json.loads(content.generation_metadata or '{}').get("template_id"),
                "generation_time": content.generation_time,
                "needs_review": content.needs_review,
                "is_winner": variant.variant_index == test.winner_index
            })

        return {
            "test_id": test.id,
            "brief_id": test.brief_id,
            "status": test.status,
            "variants": variant_data,
            "winner_index": test.winner_index,
            "metrics": json.loads(test.metrics_json) if test.metrics_json else {},
            "created_at": test.created_at.isoformat(),
            "completed_at": test.completed_at.isoformat() if test.completed_at else None
        }
2. app/services/crew_service.py Update
python

Collapse

Wrap

Copy
# app/services/crew_service.py (partial update)
import time
# ... (other imports remain)

class ContentCrewService:
    def run_crew(self, save_to_db=True, force_model: Optional[str] = None, template_id: Optional[str] = None):
        try:
            brief = self._get_brief_data()
            model = force_model or self._select_model(brief)
            start_time = time.time()  # Track generation time

            if template_id:
                template = self.template_service.get_template(template_id)
                if template:
                    system_prompt, user_prompt = self.template_service.fill_template(template, brief)
                    logger.info(f"Using template {template.name} (ID: {template_id})")
                else:
                    logger.warning(f"Template {template_id} not found, using default prompts")
                    system_prompt, user_prompt = self._create_prompts(brief)
            else:
                system_prompt, user_prompt = self._create_prompts(brief)

            logger.info(f"Generating content for topic: {brief.get('topic')} with model: {model}")
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=self._calculate_tokens(brief.get('word_count', 500)),
            )
            generated_content = response.choices[0].message.content
            generation_time = time.time() - start_time

            if save_to_db and self.brief_id:
                content_id = self._save_to_database(generated_content, model, template_id, generation_time)
                return content_id
            return generated_content

        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            return self._generate_error_content(brief, str(e))

    def _save_to_database(self, content_text: str, model_used: str, 
                         template_id: Optional[str] = None, generation_time: float = None) -> str:
        db = next(get_db())
        metadata = {"template_id": template_id, "template_name": self.template_service.get_template(template_id).name if template_id else None}
        content = Content(
            id=str(uuid.uuid4()),
            brief_id=self.brief_id,
            generated_text=content_text,
            delivery_status="pending",
            model_used=model_used,
            generation_metadata=json.dumps(metadata) if metadata else None,
            generation_time=generation_time,  # New field
            needs_review=True,  # Default flag for manual review
            created_at=datetime.utcnow()
        )
        db.add(content)
        db.commit()
        return content.id
3. app/db/models.py Extension
python

Collapse

Wrap

Copy
# app/db/models.py (partial update)
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Float, Boolean

class Content(Base):
    __tablename__ = "content"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    brief_id = Column(String, ForeignKey("briefs.id"))
    generated_text = Column(Text)
    quality_score = Column(Float, nullable=True)
    delivery_status = Column(String)
    model_used = Column(String, nullable=True)
    generation_metadata = Column(Text, nullable=True)
    generation_time = Column(Float, nullable=True)  # New: seconds to generate
    needs_review = Column(Boolean, default=True)  # New: flag for manual review
    created_at = Column(DateTime, default=datetime.utcnow)
    ab_test_variants = relationship("ABTestVariant", back_populates="content")

class ABTest(Base):
    __tablename__ = "ab_tests"
    # Existing fields remain unchanged
4. Alembic Migration (alembic/versions/20250329_add_ab_test_metrics.py)
python

Collapse

Wrap

Copy
# alembic/versions/20250329_add_ab_test_metrics.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('content', sa.Column('generation_time', sa.Float(), nullable=True))
    op.add_column('content', sa.Column('needs_review', sa.Boolean(), default=True))

def downgrade():
    op.drop_column('content', 'needs_review')
    op.drop_column('content', 'generation_time')
5. app/api/ab_testing.py
python

Collapse

Wrap

Copy
# app/api/ab_testing.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from pydantic import BaseModel
from app.db.database import get_db
from app.services.ab_testing_service import ABTestingService
from app.services.auth_service import get_admin_user

router = APIRouter(prefix="/api", tags=["ab-testing"])

class Variant(BaseModel):
    model: Optional[str] = None
    template_id: Optional[str] = None

class ABTestCreate(BaseModel):
    brief_id: str
    variants: List[Variant]

class ABTestResult(BaseModel):
    test_id: str
    brief_id: str
    status: str
    variants: List[Dict]
    winner_index: Optional[int]
    metrics: Dict

@router.post("/admin/ab-tests", response_model=dict)
async def create_ab_test(test: ABTestCreate, db: Session = Depends(get_db), _ = Depends(get_admin_user)):
    """Create a new A/B test (admin only)."""
    service = ABTestingService(db)
    test_id = await service.create_test(test.brief_id, [v.dict() for v in test.variants])
    return {"test_id": test_id}

@router.post("/admin/ab-tests/{test_id}/select-winner", response_model=dict)
async def select_winner(test_id: str, winner_index: int, metrics: Dict = {}, 
                      db: Session = Depends(get_db), _ = Depends(get_admin_user)):
    """Select the winning variant (admin only)."""
    service = ABTestingService(db)
    success = await service.select_winner(test_id, winner_index, metrics)
    if not success:
        raise HTTPException(status_code=404, detail="Test not found")
    return {"status": "success"}

@router.get("/admin/ab-test-results/{test_id}", response_model=ABTestResult)
async def get_test_results(test_id: str, db: Session = Depends(get_db), _ = Depends(get_admin_user)):
    """Get A/B test results (admin only)."""
    service = ABTestingService(db)
    results = await service.get_test_results(test_id)
    if not results:
        raise HTTPException(status_code=404, detail="Test not found")
    return results
Testing Plan
Test Creation:
POST /admin/ab-tests: {"brief_id": "<id>", "variants": [{"model": "anthropic/claude-3-sonnet-20240229"}, {"model": "mistralai/mistral-large-latest"}]} → Verify 2 content pieces generated.
Content Generation:
Check Content table for generation_time and needs_review.
Winner Selection:
POST /admin/ab-tests/<test_id>/select-winner: {"winner_index": 0, "metrics": {"quality_score": 85}} → Verify status updates.
Results:
GET /admin/ab-test-results/<test_id> → Confirm variant details and metrics.
Setup in VS Code
Dependencies: Add time (standard library) if not already used.
Migration: alembic revision -m "add ab test metrics" → Paste script, then alembic upgrade head.
Run: uvicorn main:app --reload.
Test: Use Postman with admin token for API calls.
Benefits and Metrics
Quality: Identifies best model-template pairs, targeting <15% manual review.
Efficiency: Tracks generation_time to optimize speed.
Metrics: Logs needs_review and custom metrics (e.g., quality score) for analysis.
Next Steps Post-Sprint 3
Sprint 4 (Weeks 8-10): Build dashboard backend with JWT auth.
Validation: Run 5 A/B tests, analyze results to refine model/template choices.
Improvement: Add automated quality scoring (e.g., spaCy coherence) to select_winner.