import uuid
from calendar import monthrange
from datetime import datetime, date
from venv import logger

from sqlalchemy import func

from src.exceptions import (
    DiaryTextEmptyError,
    DiaryTextTooLongError,
    DiaryFutureDateError,
    DiaryInternalErrorHTTPException,
    DiaryInvalidDateFormatError,
    DiaryInvalidTimestampError
)
from src.schemas.diary import Diary, DiaryRequestAdd, DiaryDateRequestAdd
from src.services.base import BaseService


class DiaryService(BaseService):
    MAX_TEXT_LENGTH = 1000


    def _validate_text(self, text: str):
        if not text.strip():
            raise DiaryTextEmptyError()
        if len(text) > self.MAX_TEXT_LENGTH:
            raise DiaryTextTooLongError(
                f"Максимальная длина текста - {self.MAX_TEXT_LENGTH} символов"
            )


    def _validate_date(self, date_obj: datetime):
        """Валидация даты записи"""
        if date_obj > datetime.now():
            raise DiaryFutureDateError()


    async def add_diary(self, data: DiaryRequestAdd, user_id: uuid.UUID):
        try:
            self._validate_text(data.text)

            diary = Diary(
                id=uuid.uuid4(),
                text=data.text,
                created_at=datetime.now(),
                user_id=user_id
            )
            await self.db.diary.add(diary)
            await self.db.commit()
        except DiaryTextEmptyError:
            raise
        except DiaryTextTooLongError:
            raise
        except Exception as e:
            logger.error(f"Ошибка добавления записи: {str(e)}")
            raise DiaryInternalErrorHTTPException()


    async def get_diary(self, user_id: uuid.UUID):
        return await self.db.diary.get_filtered(self.db.diary.model.user_id == user_id)


    async def add_diary_with_date(self, data: DiaryDateRequestAdd, user_id: uuid.UUID):
        try:
            self._validate_text(data.text)
            try:
                newday = datetime.strptime(data.day, '%Y-%m-%d')
            except ValueError:
                raise DiaryInvalidDateFormatError()

            self._validate_date(newday)

            diary = Diary(
                id=uuid.uuid4(),
                text=data.text,
                created_at=newday,
                user_id=user_id
            )
            await self.db.diary.add(diary)
            await self.db.commit()
        except DiaryTextEmptyError:
            raise
        except DiaryTextTooLongError:
            raise
        except DiaryInvalidDateFormatError:
            raise
        except DiaryFutureDateError:
            raise
        except Exception as e:
            logger.error(f"Ошибка добавления записи с датой: {str(e)}")
            raise DiaryInternalErrorHTTPException()


    async def get_diary_by_day(self, day: str, user_id: uuid.UUID):
        try:
            target_date = datetime.strptime(day, '%Y-%m-%d').date()
        except ValueError:
            raise DiaryInvalidDateFormatError()

        return await self.db.diary.get_filtered(
            func.date(self.db.diary.model.created_at) == target_date,
            user_id=user_id
        )


    async def get_diary_for_month(self, timestamp: int, user_id: uuid.UUID):
        try:
            if timestamp <= 0:
                raise DiaryInvalidTimestampError()

            target_date = datetime.utcfromtimestamp(timestamp)
            year, month = target_date.year, target_date.month

            first_day = datetime(year, month, 1)
            last_day = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)

            entries = await self.db.diary.get_filtered(
                self.db.diary.model.created_at >= first_day,
                self.db.diary.model.created_at < last_day,
                user_id=user_id
            )

            entry_dates = {e.created_at.date() for e in entries}

            return [
                {
                    "date": int(datetime(year, month, day).timestamp()),
                    "diary": date(year, month, day) in entry_dates
                }
                for day in range(1, monthrange(year, month)[1] + 1)
            ]
        except DiaryInvalidTimestampError:
            raise
        except Exception as e:
            logger.error(f"Ошибка получения данных за месяц: {str(e)}")
            raise DiaryInternalErrorHTTPException()
