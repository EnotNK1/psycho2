import uuid
from sqlalchemy import select, exists, and_, delete
from sqlalchemy.orm import selectinload

from src.models.training_exercises import (
    TrainingCompletedExerciseOrm
)
from src.repositories.base import BaseRepository


class TrainingCompletedExerciseRepository(BaseRepository):
    model = TrainingCompletedExerciseOrm
