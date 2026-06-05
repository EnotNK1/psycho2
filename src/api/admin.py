import csv
import json
from datetime import date, datetime
from io import StringIO
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from src.api.dependencies.admin import verify_admin
from src.api.dependencies.db import DBDep
from src.exceptions import ObjectNotFoundException
from src.models import UsersOrm
from src.models.exercise import CompletedExerciseOrm
from src.models.tests import TestResultOrm
from src.services.diary import DiaryService
from src.services.exercise import ExerciseService
from src.services.mood_tracker import MoodTrackerService
from src.services.statistics import StatisticsService

router = APIRouter(prefix="/admin", tags=["Админка"])


def convert_to_csv(data: List[dict]) -> str:
    """Конвертирует список словарей в CSV-строку с BOM для Excel."""
    if not data:
        return ""

    output = StringIO()
    output.write("\ufeff")

    fieldnames = set()
    for item in data:
        fieldnames.update(item.keys())
    fieldnames = sorted(fieldnames)

    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=";")
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
    if hasattr(model_instance, "__table__"):
        return {
            column.name: getattr(model_instance, column.name)
            for column in model_instance.__table__.columns
        }
    if hasattr(model_instance, "_asdict"):
        return model_instance._asdict()
    if hasattr(model_instance, "model_dump"):
        return model_instance.model_dump()
    if hasattr(model_instance, "__dict__"):
        return {
            key: value
            for key, value in model_instance.__dict__.items()
            if not key.startswith("_")
        }
    return dict(model_instance)


def parse_date_filter(value: Optional[str]):
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Неверный формат даты. Используйте YYYY-MM-DD",
        )


def validate_date_period(date_from, date_to):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=400,
            detail="Дата начала периода не может быть позже даты окончания",
        )


def validate_format(format_value: Optional[str]):
    if format_value not in (None, "json", "csv"):
        raise HTTPException(
            status_code=400,
            detail="Неверный формат вывода. Используйте json или csv",
        )


def serialize_row_mapping(row) -> dict:
    return dict(row._mapping)


def no_data_response(message: str):
    return {"message": message, "data": []}


def csv_response(data: list[dict], filename: str):
    csv_data = convert_to_csv(data)
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def raise_admin_error(error: Exception):
    if isinstance(error, HTTPException):
        raise error
    raise HTTPException(
        status_code=500,
        detail=f"Ошибка при обработке запроса админки: {str(error)}",
    )


@router.get("/users")
async def get_all_users(
    db: DBDep,
    admin_id: UUID = Depends(verify_admin),
    format: Optional[str] = Query(None, description="Формат вывода: json или csv"),
):
    try:
        validate_format(format)
        users = await db.users.get_all()

        if not users:
            return no_data_response("Пользователи не найдены")

        if format == "csv":
            return csv_response([model_to_dict(user) for user in users], "users.csv")

        return users
    except Exception as ex:
        raise_admin_error(ex)


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
    format: Optional[str] = Query(None, description="Формат вывода: json или csv"),
):
    try:
        validate_format(format)
        filters = []

        if company:
            filters.append(UsersOrm.company == company)
        if department:
            filters.append(UsersOrm.department == department)
        if job_title:
            filters.append(UsersOrm.job_title == job_title)
        if gender:
            filters.append(UsersOrm.gender == gender)

        if age_from is not None and age_from < 0:
            raise HTTPException(status_code=400, detail="Минимальный возраст не может быть отрицательным")
        if age_to is not None and age_to < 0:
            raise HTTPException(status_code=400, detail="Максимальный возраст не может быть отрицательным")
        if age_from is not None and age_to is not None and age_from > age_to:
            raise HTTPException(status_code=400, detail="Минимальный возраст не может быть больше максимального")

        today = date.today()
        if age_from is not None:
            max_birth_date = date(today.year - age_from, today.month, today.day)
            filters.append(UsersOrm.birth_date <= max_birth_date)
        if age_to is not None:
            min_birth_date = date(today.year - age_to - 1, today.month, today.day)
            filters.append(UsersOrm.birth_date >= min_birth_date)

        users = await db.users.get_filtered(*filters)

        if not users:
            return no_data_response("Пользователи по заданным фильтрам не найдены")

        if format == "csv":
            return csv_response([model_to_dict(user) for user in users], "filtered_users.csv")

        return users
    except Exception as ex:
        raise_admin_error(ex)


@router.get("/diary")
async def get_diary_admin(
    db: DBDep,
    admin_id: UUID = Depends(verify_admin),
    user_id: Optional[UUID] = Query(None, description="Фильтр по ID пользователя"),
    day: Optional[str] = Query(None, description="Фильтр по дате (YYYY-MM-DD)"),
    format: Optional[str] = Query(None, description="Формат вывода: json или csv"),
):
    try:
        validate_format(format)
        diary_service = DiaryService(db)
        filters = []

        if user_id:
            filters.append(diary_service.db.diary.model.user_id == user_id)

        target_date = parse_date_filter(day)
        if target_date:
            filters.append(func.date(diary_service.db.diary.model.created_at) == target_date)

        diaries = await diary_service.db.diary.get_filtered(*filters)

        if not diaries:
            return no_data_response("Дневники не найдены")

        if format == "csv":
            return csv_response([model_to_dict(diary) for diary in diaries], "diaries.csv")

        return diaries
    except Exception as ex:
        raise_admin_error(ex)


@router.get("/mood_tracker")
async def get_mood_tracker_admin(
    db: DBDep,
    admin_id: UUID = Depends(verify_admin),
    user_id: Optional[UUID] = Query(None, description="Фильтр по ID пользователя"),
    day: Optional[str] = Query(None, description="Фильтр по дате (YYYY-MM-DD)"),
    format: Optional[str] = Query(None, description="Формат вывода: json или csv"),
):
    try:
        validate_format(format)
        mood_tracker_service = MoodTrackerService(db)
        filters = []

        if user_id:
            filters.append(mood_tracker_service.db.mood_tracker.model.user_id == user_id)

        target_date = parse_date_filter(day)
        if target_date:
            filters.append(func.date(mood_tracker_service.db.mood_tracker.model.created_at) == target_date)

        mood_tracker = await mood_tracker_service.db.mood_tracker.get_filtered(*filters)

        if not mood_tracker:
            return no_data_response("Записи трекера настроения не найдены")

        if format == "csv":
            return csv_response([model_to_dict(mood) for mood in mood_tracker], "mood_tracker.csv")

        return mood_tracker
    except Exception as ex:
        raise_admin_error(ex)


@router.get("/exercises")
async def get_exercises_admin(
    db: DBDep,
    admin_id: UUID = Depends(verify_admin),
    user_id: Optional[UUID] = Query(None, description="Фильтр по ID пользователя"),
    day: Optional[str] = Query(None, description="Фильтр по дате (YYYY-MM-DD)"),
    exercise_type: Optional[str] = Query(None, description="Фильтр по типу упражнения"),
    format: Optional[str] = Query(None, description="Формат вывода: json или csv"),
):
    try:
        validate_format(format)
        exercise_service = ExerciseService(db)
        filters = []

        if user_id:
            filters.append(exercise_service.db.exercise.model.user_id == user_id)

        target_date = parse_date_filter(day)
        if target_date:
            filters.append(func.date(exercise_service.db.exercise.model.created_at) == target_date)

        if exercise_type:
            filters.append(exercise_service.db.exercise.model.exercise_type == exercise_type)

        exercises = await exercise_service.db.exercise.get_filtered(*filters)

        if not exercises:
            return no_data_response("Записи упражнений не найдены")

        if format == "csv":
            return csv_response([model_to_dict(exercise) for exercise in exercises], "exercises.csv")

        return exercises
    except Exception as ex:
        raise_admin_error(ex)


@router.get("/passed-tests")
async def get_passed_tests_admin(
    db: DBDep,
    admin_id: UUID = Depends(verify_admin),
    user_id: Optional[UUID] = Query(None, description="Фильтр по ID пользователя"),
    date_from: Optional[str] = Query(None, description="Дата начала периода (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Дата окончания периода (YYYY-MM-DD)"),
    format: Optional[str] = Query(None, description="Формат вывода: json или csv"),
):
    try:
        validate_format(format)
        filters = []

        if user_id:
            filters.append(TestResultOrm.user_id == user_id)

        parsed_date_from = parse_date_filter(date_from)
        parsed_date_to = parse_date_filter(date_to)
        validate_date_period(parsed_date_from, parsed_date_to)

        if parsed_date_from:
            filters.append(func.date(TestResultOrm.date) >= parsed_date_from)
        if parsed_date_to:
            filters.append(func.date(TestResultOrm.date) <= parsed_date_to)

        result = await db.session.execute(
            select(
                TestResultOrm.id,
                TestResultOrm.user_id,
                TestResultOrm.test_id,
                TestResultOrm.date,
            )
            .where(*filters)
            .order_by(TestResultOrm.date.desc())
        )
        passed_tests = [serialize_row_mapping(row) for row in result.all()]

        if not passed_tests:
            return no_data_response("Пройденные тесты не найдены")

        if format == "csv":
            return csv_response(passed_tests, "passed_tests.csv")

        return passed_tests
    except Exception as ex:
        raise_admin_error(ex)


@router.get("/passed-exercises")
async def get_passed_exercises_admin(
    db: DBDep,
    admin_id: UUID = Depends(verify_admin),
    user_id: Optional[UUID] = Query(None, description="Фильтр по ID пользователя"),
    date_from: Optional[str] = Query(None, description="Дата начала периода (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Дата окончания периода (YYYY-MM-DD)"),
    format: Optional[str] = Query(None, description="Формат вывода: json или csv"),
):
    try:
        validate_format(format)
        filters = []

        if user_id:
            filters.append(CompletedExerciseOrm.user_id == user_id)

        parsed_date_from = parse_date_filter(date_from)
        parsed_date_to = parse_date_filter(date_to)
        validate_date_period(parsed_date_from, parsed_date_to)

        if parsed_date_from:
            filters.append(func.date(CompletedExerciseOrm.date) >= parsed_date_from)
        if parsed_date_to:
            filters.append(func.date(CompletedExerciseOrm.date) <= parsed_date_to)

        result = await db.session.execute(
            select(
                CompletedExerciseOrm.id,
                CompletedExerciseOrm.user_id,
                CompletedExerciseOrm.exercise_structure_id,
                CompletedExerciseOrm.date,
            )
            .where(*filters)
            .order_by(CompletedExerciseOrm.date.desc())
        )
        passed_exercises = [serialize_row_mapping(row) for row in result.all()]

        if not passed_exercises:
            return no_data_response("Пройденные упражнения не найдены")

        if format == "csv":
            return csv_response(passed_exercises, "passed_exercises.csv")

        return passed_exercises
    except Exception as ex:
        raise_admin_error(ex)


@router.get("/user-statistics/{user_id}")
async def get_user_statistics(
    user_id: UUID,
    db: DBDep,
    admin_id: UUID = Depends(verify_admin),
    format: Optional[str] = Query(None, description="Формат вывода: json или csv"),
):
    try:
        validate_format(format)
        statistics_service = StatisticsService(db)
        statistics = await statistics_service.get_user_activity_statistics(user_id)

        if not statistics:
            return no_data_response("Статистика пользователя не найдена")

        if format == "csv":
            statistics_data = [statistics] if isinstance(statistics, dict) else statistics
            processed_statistics = []

            for item in statistics_data:
                processed_item = {}
                for key, value in item.items():
                    if isinstance(value, (dict, list)):
                        processed_item[key] = json.dumps(value, ensure_ascii=False, indent=None)
                    else:
                        processed_item[key] = value
                processed_statistics.append(processed_item)

            return csv_response(processed_statistics, f"statistics_{user_id}.csv")

        return JSONResponse(
            content=statistics,
            media_type="application/json; charset=utf-8",
        )
    except ObjectNotFoundException:
        return no_data_response("Пользователь или данные не найдены")
    except Exception as ex:
        raise_admin_error(ex)
