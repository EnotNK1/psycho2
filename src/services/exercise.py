from typing import List, Optional
import logging
import uuid
from fastapi import HTTPException, status
from src.services.base import BaseService
from src.schemas.exercise import (
    ExerciseResponse, ExerciseDetailResponse,
    FieldResponse, VariantResponse, CompletedExerciseCreate,
    ExerciseCreate, FieldCreate, VariantCreate
)
from src.exceptions import ObjectNotFoundHTTPException

logger = logging.getLogger(__name__)


class ExerciseService(BaseService):
    async def create_exercise(self, exercise_data: ExerciseCreate) -> ExerciseResponse:
        return await self.db.exercise.create_exercise(exercise_data)

    async def create_field(self, exercise_id: uuid.UUID, field_data: FieldCreate) -> FieldResponse:
        if not await self.db.exercise.exercise_exists(exercise_id):
            raise ObjectNotFoundHTTPException
        return await self.db.exercise.create_field(exercise_id, field_data)

    async def create_variant(self, field_id: uuid.UUID, variant_data: VariantCreate) -> VariantResponse:
        field = await self.db.exercise.get_field(field_id)
        if not field:
            raise ObjectNotFoundHTTPException
        return await self.db.exercise.create_variant(field_id, variant_data)

    async def get_all_exercises(self, user_id: Optional[uuid.UUID] = None) -> List[ExerciseResponse]:
        return await self.db.exercise.get_all_exercises(user_id)

    async def get_exercise_by_id(self, exercise_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> ExerciseDetailResponse:
        exercise = await self.db.exercise.get_exercise_by_id(exercise_id, user_id)
        if not exercise:
            raise ObjectNotFoundHTTPException
        return exercise

    async def complete_exercise(self, user_id: uuid.UUID, completed_data: CompletedExerciseCreate) -> None:
        try:
            await self.db.exercise.complete_exercise(user_id, completed_data)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error completing exercise: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
