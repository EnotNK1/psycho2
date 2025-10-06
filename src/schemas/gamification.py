from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class ScoreEntry(BaseModel):
    date: str  # ISO format date "YYYY-MM-DD"
    score: int  # 0-40


class CurrentScoreResponse(BaseModel):
    score: int


class WeeklyScoresResponse(BaseModel):
    scores: List[ScoreEntry]


class PeriodScoresResponse(BaseModel):
    scores: List[ScoreEntry]


class AddPointsRequest(BaseModel):
    activity_type: str  # "test_completed", "exercise_done", "theory_read"