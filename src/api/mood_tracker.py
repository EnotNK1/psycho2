import uuid
from fastapi import APIRouter, Query
from src.schemas.mood_tracker import MoodTrackerDateRequestAdd
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.services.mood_tracker import MoodTrackerService

from src.exceptions import (
    MoodScoreOutOfRangeHTTPException,
    MoodTrackerDateFormatHTTPException,
    MoodTrackerNotFoundHTTPException,
    MoodTrackerNotOwnedHTTPException,
    MoodTrackerInternalErrorHTTPException,
    MoodTrackerDateFormatError,
    MoodTrackerNotFoundError,
    MoodTrackerNotOwnedError,
    MoodScoreOutOfRangeError,
    MoodTrackerFutureDateError,
    MoodTrackerFutureDateHTTPException
)

router = APIRouter(prefix="/mood_tracker", tags=["Трекер настроения"])


@router.post("")
async def save_mood_tracker(db: DBDep, user_id: UserIdDep, data: MoodTrackerDateRequestAdd):
    try:
        await MoodTrackerService(db).save_mood_tracker(data, user_id)
        return {"status": "OK"}
    except MoodScoreOutOfRangeError:
        raise MoodScoreOutOfRangeHTTPException
    except MoodTrackerDateFormatError:
        raise MoodTrackerDateFormatHTTPException
    except MoodTrackerFutureDateError:
        raise MoodTrackerFutureDateHTTPException
    except Exception:
        raise MoodTrackerInternalErrorHTTPException


@router.get("")
async def get_mood_tracker(
    db: DBDep,
    user_id: UserIdDep,
    day: str = Query(None, title="Date", description="Дата в формате YYYY-MM-DD")
):
    try:
        return await MoodTrackerService(db).get_mood_diary(day, user_id)
    except MoodTrackerDateFormatError:
        raise MoodTrackerDateFormatHTTPException
    except Exception:
        raise MoodTrackerInternalErrorHTTPException


@router.get("/{mood_tracker_id}")
async def get_mood_tracker_by_id(
    mood_tracker_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep
):
    try:
        return await MoodTrackerService(db).get_mood_tracker_by_id(mood_tracker_id, user_id)
    except MoodTrackerNotFoundError:
        raise MoodTrackerNotFoundHTTPException
    except MoodTrackerNotOwnedError:
        raise MoodTrackerNotOwnedHTTPException
    except Exception:
        raise MoodTrackerInternalErrorHTTPException
