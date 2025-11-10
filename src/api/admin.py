from http.client import HTTPException
from operator import and_
import csv
from io import StringIO
import json

from fastapi import APIRouter, Depends, Query, Response
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


def convert_to_csv(data: List[dict]) -> str:
    """Конвертирует список словарей в CSV строку с BOM для Excel"""
    if not data:
        return ""

    output = StringIO()

    output.write('\ufeff')

    fieldnames = set()
    for item in data:
        fieldnames.update(item.keys())
    fieldnames = sorted(fieldnames)

    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()

    for row in data:
        processed_row = {}
        for key, value in row.items():
            if value is None:
                processed_row[key] = ""
            elif isinstance(value, (dict, list)):
                processed_row[key] = json.dumps(value, ensure_ascii=False, indent=None)
            elif isinstance(value, (datetime, date)):
                processed_row[key] = value.isoformat()
            elif isinstance(value, UUID):
                processed_row[key] = str(value)
            else:
                processed_row[key] = str(value)

        writer.writerow(processed_row)

    return output.getvalue()


def model_to_dict(model_instance):
    if hasattr(model_instance, '__table__'):
        return {c.name: getattr(model_instance, c.name) for c in model_instance.__table__.columns}
    elif hasattr(model_instance, '_asdict'):
        return model_instance._asdict()
    elif hasattr(model_instance, '__dict__'):
        result = {}
        for key, value in model_instance.__dict__.items():
            if not key.startswith('_'):
                result[key] = value
        return result
    else:
        return dict(model_instance)


@router.get("/users", response_model=List[AdminUserResponse])
async def get_all_users(
        db: DBDep,
        admin_id: UUID = Depends(verify_admin),
        format: Optional[str] = Query(None, description="Формат вывода: json или csv")
):
    users = await db.users.get_all()

    if format == "csv":
        users_data = [model_to_dict(user) for user in users]
        csv_data = convert_to_csv(users_data)

        return Response(
            content=csv_data,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=users.csv"}
        )

    return users


@router.get("/users/filter")
async def get_users_with_filters(
        db: DBDep,
        admin_id: UUID = Depends(verify_admin),
        company: Optional[str] = Query(None),
        department: Optional[str] = Query(None),
        job_title: Optional[str] = Query(None),
        age_from: Optional[int] = Query(None),
        age_to: Optional[int] = Query(None),
        gender: Optional[str] = Query(None),
        format: Optional[str] = Query(None, description="Формат вывода: json или csv")
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

    users = await db.users.get_filtered(*filters)

    if format == "csv":
        users_data = [model_to_dict(user) for user in users]
        csv_data = convert_to_csv(users_data)

        return Response(
            content=csv_data,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=filtered_users.csv"}
        )

    return users


@router.get("/diary")
async def get_diary_admin(
        db: DBDep,
        admin_id: UUID = Depends(verify_admin),
        user_id: Optional[UUID] = Query(None, description="Фильтр по ID пользователя"),
        day: Optional[str] = Query(None, description="Фильтр по дате (YYYY-MM-DD)"),
        format: Optional[str] = Query(None, description="Формат вывода: json или csv")
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

    if format == "csv":
        diaries_data = [model_to_dict(diary) for diary in diaries]
        csv_data = convert_to_csv(diaries_data)

        return Response(
            content=csv_data,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=diaries.csv"}
        )

    return diaries


@router.get("/mood_tracker")
async def get_mood_tracker_admin(
        db: DBDep,
        admin_id: UUID = Depends(verify_admin),
        user_id: Optional[UUID] = Query(None, description="Фильтр по ID пользователя"),
        day: Optional[str] = Query(None, description="Фильтр по дате (YYYY-MM-DD)"),
        format: Optional[str] = Query(None, description="Формат вывода: json или csv")
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

    if format == "csv":
        mood_data = [model_to_dict(mood) for mood in mood_tracker]
        csv_data = convert_to_csv(mood_data)

        return Response(
            content=csv_data,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=mood_tracker.csv"}
        )

    return mood_tracker


@router.get("/exercises")
async def get_exercises_admin(
        db: DBDep,
        admin_id: UUID = Depends(verify_admin),
        user_id: Optional[UUID] = Query(None, description="Фильтр по ID пользователя"),
        day: Optional[str] = Query(None, description="Фильтр по дате (YYYY-MM-DD)"),
        exercise_type: Optional[str] = Query(None, description="Фильтр по типу упражнения"),
        format: Optional[str] = Query(None, description="Формат вывода: json или csv")
):
    exercise_service = ExerciseService(db)
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

    if format == "csv":
        exercises_data = [model_to_dict(exercise) for exercise in exercises]
        csv_data = convert_to_csv(exercises_data)

        return Response(
            content=csv_data,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=exercises.csv"}
        )

    return exercises


@router.get("/user-statistics/{user_id}")
async def get_user_statistics(
        user_id: UUID,
        db: DBDep,
        admin_id: UUID = Depends(verify_admin),
        format: Optional[str] = Query(None, description="Формат вывода: json или csv")
):
    statistics_service = StatisticsService(db)

    try:
        statistics = await statistics_service.get_user_activity_statistics(user_id)

        if not statistics:
            raise ObjectNotFoundHTTPException(detail="Статистика не найдена")

        if format == "csv":
            if isinstance(statistics, dict):
                statistics_data = [statistics]
            else:
                statistics_data = statistics

            processed_statistics = []
            for item in statistics_data:
                processed_item = {}
                for key, value in item.items():
                    if isinstance(value, (dict, list)):
                        processed_item[key] = json.dumps(value, ensure_ascii=False, indent=None)
                    else:
                        processed_item[key] = value
                processed_statistics.append(processed_item)

            csv_data = convert_to_csv(processed_statistics)

            return Response(
                content=csv_data,
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": f"attachment; filename=statistics_{user_id}.csv"}
            )

        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=statistics,
            media_type="application/json; charset=utf-8"
        )

    except ObjectNotFoundException as ex:
        raise ObjectNotFoundHTTPException(detail="Пользователь или данные не найдены")