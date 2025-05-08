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
from src.schemas.diary import DiaryDateRequestAdd
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.services.diary import DiaryService

router = APIRouter(prefix="/diary", tags=["Вольный дневник(Заметки)"])


@router.get("")
async def get_diary(
    db: DBDep,
    user_id: UserIdDep,
    day: str | None = None,
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

@router.get("/by_month")
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
