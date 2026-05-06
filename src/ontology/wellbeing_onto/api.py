from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

from .recommendation_demo import generate_recommendations_from_payload

logger = logging.getLogger(__name__)
ONTOLOGY_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "ontologies"
    / "wellbeing_app_demo_rules.owl"
)


class ScaleResult(BaseModel):
    scale_title: str = Field(..., description="Название шкалы")
    score: float = Field(..., description="Числовое значение шкалы")


class RecommendationRequest(BaseModel):
    test_id: str = Field(..., description="ID теста или Tracker")
    scale_results: List[ScaleResult] = Field(default_factory=list)


def recommendations(request: RecommendationRequest):
    try:
        payload = request.model_dump(exclude_none=True)
        return generate_recommendations_from_payload(
            payload=payload,
            ontology_path=str(ONTOLOGY_PATH),
        )
    except Exception as e:
        logger.exception("Failed to generate ontology recommendations: %s", e)
        return []
