import uuid
from http.client import HTTPException

from fastapi import APIRouter

from src.schemas.mood_tracker import MoodTrackerDateRequestAdd
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.services.mood_tracker import MoodTrackerService
from datetime import date, datetime

router = APIRouter(prefix="/mood_tracker", tags=["Трекер настроения"])

@router.get("")
async def get_mood_diary(db: DBDep, day: str):
    return await MoodTrackerService(db).get_mood_diary(day)


@router.post("")
async def save_mood_tracker(db: DBDep, user_id: UserIdDep, data: MoodTrackerDateRequestAdd):
    await MoodTrackerService(db).save_mood_tracker(data, user_id)
    return {"status": "OK"}


@router.get("/{mood_tracker_id}")
async def get_mood_tracker_by_id(tracker_id: uuid.UUID, db: DBDep):
    return await MoodTrackerService(db).get_mood_tracker_by_id(tracker_id)
