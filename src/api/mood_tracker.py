import uuid
from typing import Optional
from fastapi import APIRouter, Query
from src.api.dependencies.db import DBDep
from src.api.dependencies.user_id import UserIdDep
from src.schemas.mood_tracker import MoodTrackerDateRequestAdd
from src.services.mood_tracker import MoodTrackerService
from src.services.emoji import EmojiService

from src.exceptions import (
    ScoreOutOfRangeHTTPException,
    InvalidDateFormatHTTPException,
    ObjectNotFoundHTTPException,
    NotOwnedHTTPException,
    InternalErrorHTTPException,
    ScoreOutOfRangeError,
    NotOwnedError, InvalidEmojiIdException, InvalidEmojiIdHTTPException
)

router = APIRouter(prefix="/mood_tracker", tags=["Трекер настроения"])

@router.post("")
async def add_mood_tracker(
    db: DBDep,
    user_id: UserIdDep,
    data: MoodTrackerDateRequestAdd
):
    try:
        await MoodTrackerService(db).save_mood_tracker(data, user_id)
        return {"status": "OK"}
    except ScoreOutOfRangeError:
        raise ScoreOutOfRangeHTTPException
    except InvalidEmojiIdException:
        raise InvalidEmojiIdHTTPException
    except Exception:
        raise InternalErrorHTTPException

@router.get("/emoji")
async def get_emoji(
    db: DBDep,
    emoji_id: Optional[int] = Query(None, description="ID эмодзи (опционально)")
):
    try:
        service = EmojiService(db)
        if emoji_id:
            emoji = await service.get_emoji_by_id(emoji_id)
            if not emoji:
                raise ObjectNotFoundHTTPException
            return emoji
        return await service.get_all_emojis()
    except Exception:
        raise InternalErrorHTTPException

@router.get("")
async def get_mood_tracker(
    db: DBDep,
    user_id: UserIdDep,
    day: Optional[str] = Query(None, title="Date", description="Дата в формате YYYY-MM-DD")
):
    try:
        return await MoodTrackerService(db).get_mood_tracker(day, user_id)
    except Exception:
        raise InternalErrorHTTPException

@router.get("/{mood_tracker_id}")
async def get_mood_tracker_by_id(
    mood_tracker_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep
):
    try:
        return await MoodTrackerService(db).get_mood_tracker_by_id(mood_tracker_id, user_id)
    except NotOwnedError:
        raise NotOwnedHTTPException
    except Exception:
        raise InternalErrorHTTPException


