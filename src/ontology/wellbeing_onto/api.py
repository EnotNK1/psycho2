from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .recommendation_demo import generate_recommendations_from_payload


class ScaleResult(BaseModel):
    scale_title: str = Field(..., description="Название шкалы")
    score: float = Field(..., description="Числовое значение шкалы")


class RecommendationRequest(BaseModel):
    test_id: str = Field(..., description="ID теста или Tracker")
    scale_results: List[ScaleResult] = Field(default_factory=list)


def recommendations(request: RecommendationRequest):
    try:
        payload = request.model_dump(exclude_none=True)

        result = generate_recommendations_from_payload(
            payload=payload,
            ontology_path="src/ontology/data/ontologies/wellbeing_app_demo_rules.owl",
        )

        return result
    except Exception as e:
        print(str(e))