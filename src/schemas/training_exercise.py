import uuid
from typing import List
from pydantic import BaseModel


class ExerciseShortResponse(BaseModel):
    id: uuid.UUID
    title: str
    picture_link: str | None
    is_completed: bool


class ExercisesListResponse(BaseModel):
    exercises: List[ExerciseShortResponse]


class ExerciseDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    picture_link: str | None
    description: str
    time_to_read: int
    is_completed: bool


class ExerciseCompletedResponse(BaseModel):
    is_completed: bool
