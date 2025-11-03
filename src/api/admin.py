from http.client import HTTPException
from operator import and_

from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import Optional, List
from datetime import datetime, date, timedelta

from sqlalchemy import func, select
from sqlalchemy import func
from starlette import status

from src.api.dependencies.db import DBDep
from src.api.dependencies.admin import AdminIdDep, verify_admin
from src.models import UsersOrm
from src.schemas.users import AdminUserResponse
from src.services.auth import AuthService
from src.services.diary import DiaryService
from src.services.exercise import ExerciseService
from src.services.mood_tracker import MoodTrackerService
from src.exceptions import (
    ObjectNotFoundHTTPException,
    InvalidDateFormatHTTPException, ObjectNotFoundException, InvalidPeriodHTTPException
)
from src.services.statistics import StatisticsService

router = APIRouter(prefix="/admin", tags=["Админка"])


@router.get("/users", response_model=List[AdminUserResponse])
async def get_all_users(
    db: DBDep,
    admin_id: UUID = Depends(verify_admin),
):
    return await db.users.get_all()


@router.get("/users/filter", response_model=List[AdminUserResponse])
async def get_users_with_filters(
    db: DBDep,
    admin_id: UUID = Depends(verify_admin),
    company: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    job_title: Optional[str] = Query(None),
    age_from: Optional[int] = Query(None),
    age_to: Optional[int] = Query(None),
    gender: Optional[str] = Query(None),
):
    filters = []

    if company:
        filters.append(UsersOrm.company == company)
    if department:
        filters.append(UsersOrm.department == department)
    if job_title:
        filters.append(UsersOrm.job_title == job_title)
    if gender:
        filters.append(UsersOrm.gender == gender)

    today = date.today()
    if age_from is not None:
        max_birth_date = date(today.year - age_from, today.month, today.day)
        filters.append(UsersOrm.birth_date <= max_birth_date)
    if age_to is not None:
        min_birth_date = date(today.year - age_to - 1, today.month, today.day)
        filters.append(UsersOrm.birth_date >= min_birth_date)

    return await db.users.get_filtered(*filters)


@router.get("/diary")
async def get_diary_admin(
        db: DBDep,
        admin_id: UUID = Depends(verify_admin),  # Проверка прав админа
        user_id: Optional[UUID] = Query(None, description="Фильтр по ID пользователя"),
        day: Optional[str] = Query(None, description="Фильтр по дате (YYYY-MM-DD)")
):

    diary_service = DiaryService(db)
    filters = []

    if user_id:
        filters.append(diary_service.db.diary.model.user_id == user_id)

    if day:
        try:
            target_date = datetime.strptime(day, '%Y-%m-%d').date()
            filters.append(func.date(diary_service.db.diary.model.created_at) == target_date)
        except ValueError:
            raise InvalidDateFormatHTTPException()

    diaries = await diary_service.db.diary.get_filtered(*filters)

    if not diaries:
        raise ObjectNotFoundHTTPException(detail="Дневники не найдены")

    return diaries


@router.get("/mood_tracker")
async def get_mood_tracker_admin(
        db: DBDep,
        admin_id: UUID = Depends(verify_admin),  # Проверка прав админа
        user_id: Optional[UUID] = Query(None, description="Фильтр по ID пользователя"),
        day: Optional[str] = Query(None, description="Фильтр по дате (YYYY-MM-DD)")
):
    mood_tracker_service = MoodTrackerService(db)
    filters = []

    if user_id:
        filters.append(mood_tracker_service.db.mood_tracker.model.user_id == user_id)

    if day:
        try:
            target_date = datetime.strptime(day, '%Y-%m-%d').date()
            filters.append(func.date(mood_tracker_service.db.mood_tracker.model.created_at) == target_date)
        except ValueError:
            raise InvalidDateFormatHTTPException()

    mood_tracker = await mood_tracker_service.db.mood_tracker.get_filtered(*filters)

    if not mood_tracker:
        raise ObjectNotFoundHTTPException(detail="Записи трекера настроения не найдены")

    return mood_tracker


@router.get("/exercises")
async def get_exercises_admin(
        db: DBDep,
        admin_id: UUID = Depends(verify_admin),  # Проверка прав админа
        user_id: Optional[UUID] = Query(None, description="Фильтр по ID пользователя"),
        day: Optional[str] = Query(None, description="Фильтр по дате (YYYY-MM-DD)"),
        exercise_type: Optional[str] = Query(None, description="Фильтр по типу упражнения")
):
    exercise_service = ExerciseService(db)  # Предполагается, что у вас есть ExerciseService
    filters = []

    if user_id:
        filters.append(exercise_service.db.exercise.model.user_id == user_id)

    if day:
        try:
            target_date = datetime.strptime(day, '%Y-%m-%d').date()
            filters.append(func.date(exercise_service.db.exercise.model.created_at) == target_date)
        except ValueError:
            raise InvalidDateFormatHTTPException()

    if exercise_type:
        filters.append(exercise_service.db.exercise.model.exercise_type == exercise_type)

    exercises = await exercise_service.db.exercise.get_filtered(*filters)

    if not exercises:
        raise ObjectNotFoundHTTPException(detail="Записи упражнений не найдены")

    return exercises


@router.get("/user-statistics/{user_id}")
async def get_user_statistics(
        user_id: UUID,
        db: DBDep,
        admin_id: UUID = Depends(verify_admin)
):

    statistics_service = StatisticsService(db)

    try:
        statistics = await statistics_service.get_user_activity_statistics(user_id)

        if not statistics:
            raise ObjectNotFoundHTTPException(detail="Статистика не найдена")

        return statistics

    except ObjectNotFoundException as ex:
        raise ObjectNotFoundHTTPException(detail="Пользователь или данные не найдены")
