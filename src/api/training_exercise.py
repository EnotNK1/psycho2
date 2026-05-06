import uuid
from fastapi import APIRouter, Response
from src.api.dependencies.db import DBDep
from src.api.dependencies.user_id import UserIdDep
from src.exceptions import ObjectNotFoundException, ObjectNotFoundHTTPException
from src.services.training_exercise import TrainingExerciseService
from src.schemas.training_exercise import (
    ExerciseShortResponse,
    ExercisesListResponse,
    ExerciseDetailResponse,
    ExerciseCompletedResponse
)

router = APIRouter(prefix="/training-exercises", tags=["Обучающие Упражнения"])


@router.post("/auto-create")
async def seed_exercises(
    db: DBDep,
):
    await TrainingExerciseService(db).seed_exercises()
    return {"status": "ok"}


@router.get("/")
async def get_all_exercises(
    db: DBDep,
    user_id: UserIdDep = None
):
    exercises = await TrainingExerciseService(db).get_all_exercises(user_id)
    return ExercisesListResponse(exercises=exercises)


@router.get("/{exercise_id}", response_model=ExerciseDetailResponse)
async def get_exercise(
    exercise_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep = None
):
    try:
        return await TrainingExerciseService(db).get_exercise_by_id(exercise_id, user_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException()


@router.get("/{exercise_id}/structure")
async def get_exercise_structure(
    exercise_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep = None
):
    try:
        return await TrainingExerciseService(db).get_exercise_structure_by_id(exercise_id, user_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException()


@router.get("/{exercise_id}/completed")
async def is_exercise_completed(
    exercise_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep = None
):
    return await TrainingExerciseService(db).is_exercise_completed_by_id(exercise_id, user_id)


@router.post("/{exercise_id}/complete")
async def complete_exercise(
    exercise_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep = None
):
    await TrainingExerciseService(db).complete_exercise(exercise_id, user_id)
    return {"status": "ok"}
