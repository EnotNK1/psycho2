from typing import List
import uuid
from fastapi import APIRouter, status
from src.schemas.exercise import (
    ExerciseResponse, ExerciseDetailResponse,
    FieldResponse, VariantResponse,
    ExerciseCreate, FieldCreate, VariantCreate,
    CompletedExerciseCreate
)
from src.services.exercise import ExerciseService
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep

router = APIRouter(prefix="/exercises", tags=["Упражнения"])


@router.post("/", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    exercise_data: ExerciseCreate,
    db: DBDep
):
    return await ExerciseService(db).create_exercise(exercise_data)


@router.post("/{exercise_id}/fields/", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
async def create_field(
    exercise_id: uuid.UUID,
    field_data: FieldCreate,
    db: DBDep
):
    return await ExerciseService(db).create_field(exercise_id, field_data)


@router.post("/fields/{field_id}/variants/", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
async def create_variant(
    field_id: uuid.UUID,
    variant_data: VariantCreate,
    db: DBDep
):
    return await ExerciseService(db).create_variant(field_id, variant_data)


@router.get("/", response_model=List[ExerciseResponse])
async def get_all_exercises(
    db: DBDep,
    user_id: UserIdDep = None
):
    return await ExerciseService(db).get_all_exercises(user_id)


@router.get("/{exercise_id}", response_model=ExerciseDetailResponse)
async def get_exercise(
    exercise_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep = None
):
    return await ExerciseService(db).get_exercise_by_id(exercise_id, user_id)


@router.post("/complete/", status_code=status.HTTP_201_CREATED)
async def complete_exercise(
    completed_data: CompletedExerciseCreate,
    db: DBDep,
    user_id: UserIdDep
):
    await ExerciseService(db).complete_exercise(user_id, completed_data)
    return {"status": "OK"}
