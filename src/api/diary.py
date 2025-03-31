from fastapi import Query
from fastapi import APIRouter

from src.exceptions import (
    DiaryInternalErrorHTTPException,
    DiaryFutureDateError,
    DiaryInvalidDateFormatError,
    DiaryTextTooLongError,
    DiaryTextEmptyError,
    DiaryInvalidDateFormatHTTPException,
    DiaryFutureDateHTTPException,
    DiaryTextTooLongHTTPException,
    DiaryTextEmptyHTTPException,
    DiaryInvalidTimestampError,
    DiaryInvalidTimestampHTTPException
)
from src.schemas.diary import DiaryRequestAdd, DiaryDateRequestAdd
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.services.diary import DiaryService

router = APIRouter(prefix="/diary", tags=["Вольный дневник(Заметки)"])


@router.get("")
async def get_diary(
    db: DBDep,
    user_id: UserIdDep,
):
    return await DiaryService(db).get_diary(user_id)


@router.post("")
async def create_diary(
    db: DBDep,
    user_id: UserIdDep,
    data: DiaryRequestAdd
):
    try:
        await DiaryService(db).add_diary(data, user_id)
        return {"status": "OK"}
    except DiaryTextEmptyError:
        raise DiaryTextEmptyHTTPException
    except DiaryTextTooLongError:
        raise DiaryTextTooLongHTTPException
    except Exception as e:
        raise DiaryInternalErrorHTTPException


@router.get("/with_date")
async def get_diary_by_day(
    db: DBDep,
    day: str,
    user_id: UserIdDep
):
    try:
        return await DiaryService(db).get_diary_by_day(day, user_id)
    except DiaryInvalidDateFormatError:
        raise DiaryInvalidDateFormatHTTPException
    except Exception as e:
        raise DiaryInternalErrorHTTPException


@router.post("/with_date")
async def create_diary_with_date(
    db: DBDep,
    user_id: UserIdDep,
    data: DiaryDateRequestAdd
):
    try:
        await DiaryService(db).add_diary_with_date(data, user_id)
        return {"status": "OK"}
    except DiaryTextEmptyError:
        raise DiaryTextEmptyHTTPException
    except DiaryTextTooLongError:
        raise DiaryTextTooLongHTTPException
    except DiaryInvalidDateFormatError:
        raise DiaryInvalidDateFormatHTTPException
    except DiaryFutureDateError:
        raise DiaryFutureDateHTTPException
    except Exception as e:
        raise DiaryInternalErrorHTTPException


@router.get("/by_month")
async def check_diary_for_month(
    db: DBDep,
    user_id: UserIdDep,
    timestamp: int = Query(default=..., gt=0, description="Unix timestamp")
):
    try:
        return await DiaryService(db).get_diary_for_month(timestamp, user_id)
    except DiaryInvalidTimestampError:
        raise DiaryInvalidTimestampHTTPException
    except Exception as e:
        raise DiaryInternalErrorHTTPException
