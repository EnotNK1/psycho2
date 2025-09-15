import uuid
from fastapi import APIRouter, Query
from src.schemas.mood_tracker import MoodTrackerDateRequestAdd, MoodTracker
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.services.mood_tracker import MoodTrackerService

from src.exceptions import (
    ScoreOutOfRangeHTTPException,
    InvalidDateFormatHTTPException,
    ObjectNotFoundHTTPException,
    NotOwnedHTTPException,
    InternalErrorHTTPException,
    InvalidDateFormatError,
    ObjectNotFoundException,
    NotOwnedError,
    ScoreOutOfRangeError,
    FutureDateError,
    FutureDateHTTPException
)

router = APIRouter(prefix="/mood_tracker", tags=["Трекер настроения"])


@router.post("")
async def add_mood_tracker(db: DBDep, user_id: UserIdDep, data: MoodTrackerDateRequestAdd):
    try:
        await MoodTrackerService(db).save_mood_tracker(data, user_id)
        return {"status": "OK"}
    except ScoreOutOfRangeError:
        raise ScoreOutOfRangeHTTPException
    except InvalidDateFormatError:
        raise InvalidDateFormatHTTPException
    except FutureDateError:
        raise FutureDateHTTPException
    except Exception:
        raise InternalErrorHTTPException


@router.get("",
    description="""Возвращает трекер настроения пользователя. Опциональная дата в формате YYYY-MM-DD. Если не указана, возвращается за все время.""",
    response_model=MoodTracker)
async def get_mood_tracker(
    db: DBDep,
    user_id: UserIdDep,
    day: str = Query(None, title="Date", description="Дата в формате YYYY-MM-DD")
):
    try:
        return await MoodTrackerService(db).get_mood_tracker(day, user_id)
    except InvalidDateFormatError:
        raise InvalidDateFormatHTTPException
    except Exception:
        raise InternalErrorHTTPException


@router.get("/{mood_tracker_id}",
    description="""Возвращает трекер настроения пользователя по mood_tracker_id.""",
    response_model=MoodTracker)
async def get_mood_tracker_by_id(
    mood_tracker_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep
):
    try:
        return await MoodTrackerService(db).get_mood_tracker_by_id(mood_tracker_id, user_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except NotOwnedError:
        raise NotOwnedHTTPException
    except Exception:
        raise InternalErrorHTTPException
