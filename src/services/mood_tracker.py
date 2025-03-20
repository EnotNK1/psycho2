import uuid
from ctypes import cast
from datetime import datetime, timedelta, date
from http.client import HTTPException
from sqlite3 import Date

from src.models.diary import DiaryOrm
from src.schemas.mood_tracker import MoodTracker, MoodTrackerDateRequestAdd
from src.services.base import BaseService


class MoodTrackerService(BaseService):
    async def save_mood_tracker(self, data: MoodTrackerDateRequestAdd, user_id: uuid.UUID):

        newday=datetime.strptime(data.day, '%Y-%m-%d')
        mood_tracker = MoodTracker(
            id=uuid.uuid4(),
            score=data.score,
            created_at=newday,
        )
        await self.db.mood_tracker.add(mood_tracker)
        await self.db.commit()


    async def get_mood_diary(self, day: str):

        target_date = datetime.strptime(day, '%Y-%m-%d').date()
        return await self.db.mood_tracker.get_filtered_by_date_mt(target_date)


    async def get_mood_tracker_by_id(self, tracker_id: uuid.UUID):
        return await self.db.mood_tracker.get_one(id=tracker_id)
