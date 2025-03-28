# app/schemas/ab_testing.py
from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ABTestBase(BaseModel):
    """Base model for A/B tests."""
    name: str
    description: Optional[str] = None


class ABTestCreate(ABTestBase):
    """Schema for creating an A/B test."""
    pass


class ABTestVariantBase(BaseModel):
    """Base model for A/B test variants."""
    name: str
    model: str
    prompt_template: Optional[str] = None
    parameters: Optional[Dict] = None
    weight: float = 1.0


class ABTestVariantCreate(ABTestVariantBase):
    """Schema for creating an A/B test variant."""
    pass


class ABTestWithVariantsCreate(ABTestBase):
    """Schema for creating an A/B test with variants in one operation."""
    variants: List[ABTestVariantCreate]


class ABTestVariant(ABTestVariantBase):
    """Schema for an A/B test variant."""
    id: str
    test_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ABTest(ABTestBase):
    """Schema for an A/B test."""
    id: str
    status: str
    start_date: datetime
    end_date: Optional[datetime] = None
    created_at: datetime
    variants: List[ABTestVariant] = []

    class Config:
        from_attributes = True


class ABTestRun(BaseModel):
    """Schema for running an A/B test."""
    brief_id: str
    test_id: str


class ABTestVariantRun(BaseModel):
    """Schema for running a specific A/B test variant."""
    brief_id: str
    variant_id: str


class VariantResult(BaseModel):
    """Schema for a variant result summary."""
    variant_id: str
    name: str
    model: str
    content_count: int
    avg_quality_score: Optional[float] = None
    feedback_count: int


class TestResults(BaseModel):
    """Schema for A/B test results."""
    test_id: str
    name: str
    status: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    variants: List[VariantResult] = []
