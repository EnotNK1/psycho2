import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func

from src.exceptions import (
    ScoreOutOfRangeError,
    InvalidDateFormatError,
    ObjectNotFoundException,
    NotOwnedError,
    FutureDateError
)
from src.schemas.mood_tracker import MoodTracker, MoodTrackerDateRequestAdd
from src.services.base import BaseService


class MoodTrackerService(BaseService):
    MIN_SCORE = 0
    MAX_SCORE = 100


    def _validate_score(self, score: int):
        if not (self.MIN_SCORE <= score <= self.MAX_SCORE):
            raise ScoreOutOfRangeError()


    def _validate_date(self, date_str: str):
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise InvalidDateFormatError()


    def _validate_date_not_future(self, date_obj: datetime):
        if date_obj > datetime.now():
            raise FutureDateError()

    async def save_mood_tracker(self, data: MoodTrackerDateRequestAdd, user_id: uuid.UUID):
        try:
            self._validate_score(data.score)
            self._validate_date(data.day)

            newday = datetime.strptime(data.day, '%Y-%m-%d')
            self._validate_date_not_future(newday)  # Добавляем проверку

            mood_tracker = MoodTracker(
                id=uuid.uuid4(),
                score=data.score,
                created_at=newday,
                user_id=user_id
            )
            await self.db.mood_tracker.add(mood_tracker)
            await self.db.commit()
        except (ScoreOutOfRangeError,
                InvalidDateFormatError,
                FutureDateError):
            raise
        except Exception as e:
            raise Exception(f"Ошибка при сохранении: {str(e)}")

    async def get_mood_tracker(self, day: Optional[str], user_id: uuid.UUID):
        try:
            if day:
                self._validate_date(day)
                target_date = datetime.strptime(day, '%Y-%m-%d').date()
                self._validate_date_not_future(datetime.combine(target_date, datetime.min.time()))

                return await self.db.mood_tracker.get_filtered(
                    func.date(self.db.mood_tracker.model.created_at) == target_date,
                    user_id=user_id
                )
            return await self.db.mood_tracker.get_filtered(user_id=user_id)
        except InvalidDateFormatError:
            raise
        except FutureDateError:
            raise
        except Exception as e:
            raise Exception(f"Ошибка при получении записей: {str(e)}")


    async def get_mood_tracker_by_id(self, mood_tracker_id: uuid.UUID, user_id: uuid.UUID):
        try:
            record = await self.db.mood_tracker.get_one(id=mood_tracker_id)

            if str(record.user_id) != str(user_id):
                raise NotOwnedError()

            return record
        except ObjectNotFoundException:
            raise ObjectNotFoundException()
        except Exception as e:
            raise Exception(f"Ошибка при получении записи: {str(e)}")