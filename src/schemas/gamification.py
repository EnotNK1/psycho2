from typing import List

from pydantic import BaseModel


class ScoreEntry(BaseModel):
    date: str
    score: int


class CurrentScoreResponse(BaseModel):
    score: int


class WeeklyScoresResponse(BaseModel):
    scores: List[ScoreEntry]


class PeriodScoresResponse(BaseModel):
    scores: List[ScoreEntry]


class PraiseResponse(BaseModel):
    consecutive_days: int
    title: str
    subtitle: str


class AddPointsRequest(BaseModel):
    activity_type: str
