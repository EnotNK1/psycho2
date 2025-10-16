from typing import List
import uuid
from fastapi import APIRouter, status
from src.schemas.exercise import (
    ExerciseResponse, ExerciseDetailResponse, ExerciseDetail1Response, ResultDetailResponse,
    FieldResponse, VariantResponse, ExerciseViewCreate, ExerciseResultsResponse,
    ExerciseCreate, FieldCreate, VariantCreate, ExerciseViewResponse, ResultResponse,
    CompletedExerciseCreate, ExercisesListResponse, CompletedExerciseResponse
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


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: uuid.UUID,
    db: DBDep
):
    await ExerciseService(db).delete_exercise(exercise_id)


@router.post("/{exercise_id}/fields/", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
async def create_field(
    exercise_id: uuid.UUID,
    field_data: FieldCreate,
    db: DBDep
):
    return await ExerciseService(db).create_field(exercise_id, field_data)


@router.delete("/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field(
    field_id: uuid.UUID,
    db: DBDep
):
    await ExerciseService(db).delete_field(field_id)


@router.post("/fields/{field_id}/variants/", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
async def create_variant(
    field_id: uuid.UUID,
    variant_data: VariantCreate,
    db: DBDep
):
    return await ExerciseService(db).create_variant(field_id, variant_data)


@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    variant_id: uuid.UUID,
    db: DBDep
):
    await ExerciseService(db).delete_variant(variant_id)


@router.post("/{exercise_id}/views/", response_model=ExerciseViewResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise_view(
    exercise_id: uuid.UUID,
    view_data: ExerciseViewCreate,
    db: DBDep
):
    return await ExerciseService(db).create_exercise_view(exercise_id, view_data)


@router.delete("/views/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise_view(
    view_id: uuid.UUID,
    db: DBDep
):
    await ExerciseService(db).delete_exercise_view(view_id)


@router.get("/", response_model=ExercisesListResponse)
async def get_all_exercises(
    db: DBDep,
    user_id: UserIdDep = None
):
    exercises = await ExerciseService(db).get_all_exercises(user_id)
    return ExercisesListResponse(exercises=exercises)


@router.get("/{exercise_id}", response_model=ExerciseDetailResponse)
async def get_exercise(
    exercise_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep = None
):
    return await ExerciseService(db).get_exercise_by_id(exercise_id, user_id)


@router.get("/{exercise_id}/structure", response_model=ExerciseDetail1Response)
async def get_exercise_structure(
    exercise_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep = None
):
    return await ExerciseService(db).get_exercise_structure_by_id(exercise_id, user_id)


@router.get("/{exercise_id}/results", response_model=ExerciseResultsResponse)
async def get_exercise_results(
    exercise_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep
):
    return await ExerciseService(db).get_exercise_results(exercise_id, user_id)


@router.get("/{exercise_id}/results/{result_id}", response_model=ResultDetailResponse)
async def get_exercise_result_detail(
    exercise_id: uuid.UUID,
    result_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep
):
    return await ExerciseService(db).get_exercise_result_detail(exercise_id, result_id, user_id)


@router.post("/complete/", response_model=CompletedExerciseResponse, status_code=status.HTTP_201_CREATED)
async def complete_exercise(
    completed_data: CompletedExerciseCreate,
    db: DBDep,
    user_id: UserIdDep
):
    return await ExerciseService(db).complete_exercise(user_id, completed_data)
