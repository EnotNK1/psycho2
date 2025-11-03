from pydantic import BaseModel
from typing import Dict, Any, List
from uuid import UUID


class ExerciseStatisticsResponse(BaseModel):
    total_exercises: int
    by_exercise: Dict[str, int]


class TestStatisticsResponse(BaseModel):
    total_tests: int
    by_test: Dict[str, int]


class UserStatisticsResponse(BaseModel):
    user_id: str
    exercises: ExerciseStatisticsResponse
    tests: TestStatisticsResponse
    mood_trackers_count: int
    education_blocks_count: int
    total_activities: int