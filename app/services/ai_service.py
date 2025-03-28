# app/services/ai_service.py
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ModelSelector:
    """Select the optimal AI model based on content parameters."""

    def __init__(self, config):
        self.config = config
        self.models = {
            "anthropic/claude-3-opus-20240229": {
                "strengths": ["technical", "long-form", "nuanced"],
                "cost_tier": "premium",
                "max_words": 20000,
            },
            "anthropic/claude-3-sonnet-20240229": {
                "strengths": ["balanced", "creative", "instructional"],
                "cost_tier": "standard",
                "max_words": 15000,
            },
            "mistralai/mistral-large-latest": {
                "strengths": ["efficient", "technical", "structured"],
                "cost_tier": "standard",
                "max_words": 8000,
            },
            "meta-llama/llama-3-70b-chat": {
                "strengths": ["creative", "marketing", "conversational"],
                "cost_tier": "standard",
                "max_words": 8000,
            },
            "google/gemini-pro": {
                "strengths": ["factual", "reference", "analytical"],
                "cost_tier": "standard",
                "max_words": 7000,
            }
        }

    def select_model(self, content_type: str, industry: str, length: int, budget_tier: str = "standard") -> str:
        """Select optimal model based on content parameters."""
        default_model = "anthropic/claude-3-sonnet-20240229"

        available_models = {
            name: data for name, data in self.models.items()
            if self._is_within_budget(data["cost_tier"], budget_tier) and data["max_words"] >= length
        }

        if not available_models:
            logger.warning(f"No suitable models for {content_type}/{industry}/{length} words, using default")
            return default_model

        scores = self._score_models(available_models, content_type, industry)
        if not scores:
            return default_model

        best_model = max(scores.items(), key=lambda x: x[1])[0]
        logger.info(f"Selected model: {best_model} for {content_type}/{industry}/{length}")
        return best_model

    def _is_within_budget(self, model_tier: str, budget_tier: str) -> bool:
        tier_hierarchy = {"economy": 0, "standard": 1, "premium": 2}
        return tier_hierarchy.get(model_tier, 0) <= tier_hierarchy.get(budget_tier, 1)

    def _score_models(self, models: Dict, content_type: str, industry: str) -> Dict[str, float]:
        content_type_mapping = {
            "blog": ["creative", "structured", "conversational"],
            "whitepaper": ["technical", "analytical", "reference"],
            "social": ["creative", "conversational", "marketing"],
            "newsletter": ["balanced", "instructional", "creative"],
            "technical": ["technical", "reference", "analytical"],
        }
        industry_mapping = {
            "tech": ["technical", "analytical", "factual"],
            "finance": ["analytical", "reference", "structured"],
            "health": ["factual", "reference", "nuanced"],
            "creative": ["creative", "conversational", "balanced"],
            "legal": ["nuanced", "analytical", "reference"],
        }

        relevant_strengths = (
            content_type_mapping.get(content_type.lower(), ["balanced"]) +
            industry_mapping.get(industry.lower(), ["balanced"])
        )

        scores = {}
        for model_name, model_data in models.items():
            score = sum(1 for strength in model_data["strengths"] if strength in relevant_strengths)
            scores[model_name] = score
        return scores
