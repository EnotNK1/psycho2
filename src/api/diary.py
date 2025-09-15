from fastapi import Query
from fastapi import APIRouter

from src.exceptions import (
    InternalErrorHTTPException,
    FutureDateError,
    InvalidDateFormatError,
    TextTooLongError,
    TextEmptyError,
    InvalidDateFormatHTTPException,
    FutureDateHTTPException,
    TextTooLongHTTPException,
    TextEmptyHTTPException,
    InvalidTimestampError,
    InvalidTimestampHTTPException
)
from src.schemas.diary import DiaryDateRequestAdd, Diary
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.services.diary import DiaryService

router = APIRouter(prefix="/diary", tags=["Вольный дневник(Заметки)"])


@router.get(
    "",
    description="""Возвращает записи дневника пользователя. Опциональная дата в формате YYYY-MM-DD. Если не указана, возвращаются все записи пользователя за все время.""",
    response_model = Diary
)
async def get_diary(
    db: DBDep,
    user_id: UserIdDep,
    day: str = Query(None, title="Date", description="Дата в формате YYYY-MM-DD"),
):
    try:
        return await DiaryService(db).get_diary(user_id, day)
    except InvalidDateFormatError:
        raise InvalidDateFormatHTTPException
    except Exception as e:
        raise InternalErrorHTTPException


@router.post("")
async def create_diary(
    db: DBDep,
    user_id: UserIdDep,
    data: DiaryDateRequestAdd  # Теперь используем один тип запроса с опциональной датой
):
    try:
        await DiaryService(db).add_diary(data, user_id)
        return {"status": "OK"}
    except TextEmptyError:
        raise TextEmptyHTTPException
    except TextTooLongError:
        raise TextTooLongHTTPException
    except InvalidDateFormatError:
        raise InvalidDateFormatHTTPException
    except FutureDateError:
        raise FutureDateHTTPException
    except Exception as e:
        raise InternalErrorHTTPException

@router.get("/by_month",
    description="""Получение данных о заполнении ежедневных заметок за один месяц. Ввод любого дня нужного месяца в формате Unix timestamp, обратно приходит список: 1) День в формате Unix timestamp; 2) поле diary: true/false (от первого до последнего календарного дня).""",
    response_model=DiaryDateRequestAdd)
async def get_diary_for_month(
    db: DBDep,
    user_id: UserIdDep,
    timestamp: int = Query(default=..., gt=0, description="Unix timestamp")
):
    try:
        return await DiaryService(db).get_diary_for_month(timestamp, user_id)
    except InvalidTimestampError:
        raise InvalidTimestampHTTPException
    except Exception as e:
        raise InternalErrorHTTPException
