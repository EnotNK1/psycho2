import uuid
from calendar import monthrange
from datetime import datetime, date
from venv import logger

from sqlalchemy import func

from src.exceptions import (
    TextEmptyError,
    TextTooLongError,
    FutureDateError,
    InternalErrorHTTPException,
    InvalidDateFormatError,
    InvalidTimestampError
)
from src.schemas.diary import Diary, DiaryDateRequestAdd
from src.services.base import BaseService


class DiaryService(BaseService):
    MAX_TEXT_LENGTH = 1000


    def _validate_text(self, text: str):
        if not text.strip():
            raise TextEmptyError()
        if len(text) > self.MAX_TEXT_LENGTH:
            raise TextTooLongError(
                f"Максимальная длина текста - {self.MAX_TEXT_LENGTH} символов"
            )


    def _validate_date(self, date_obj: datetime):
        """Валидация даты записи"""
        if date_obj > datetime.now():
            raise FutureDateError()

    async def add_diary(self, data: DiaryDateRequestAdd, user_id: uuid.UUID):
        try:
            self._validate_text(data.text)

            # Если дата передана, парсим и валидируем её
            if data.day:
                try:
                    created_at = datetime.strptime(data.day, '%Y-%m-%d')
                    self._validate_date(created_at)
                except ValueError:
                    raise InvalidDateFormatError()
            else:
                # Если дата не передана, используем текущее время
                created_at = datetime.now()

            diary = Diary(
                id=uuid.uuid4(),
                text=data.text,
                created_at=created_at,
                user_id=user_id
            )

            await self.db.diary.add(diary)
            await self.db.commit()

        except TextEmptyError:
            raise
        except TextTooLongError:
            raise
        except InvalidDateFormatError:
            raise
        except FutureDateError:
            raise
        except Exception as e:
            logger.error(f"Ошибка добавления записи: {str(e)}")
            raise InternalErrorHTTPException()


    async def get_diary(self, user_id: uuid.UUID, day: str | None = None):
        filters = [self.db.diary.model.user_id == user_id]

        if day:
            try:
                target_date = datetime.strptime(day, '%Y-%m-%d').date()
                filters.append(func.date(self.db.diary.model.created_at) == target_date)
            except ValueError:
                raise InvalidDateFormatError()

        return await self.db.diary.get_filtered(*filters)


    async def get_diary_for_month(self, timestamp: int, user_id: uuid.UUID):
        try:
            if timestamp <= 0:
                raise InvalidTimestampError()

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
        except InvalidTimestampError:
            raise
        except Exception as e:
            logger.error(f"Ошибка получения данных за месяц: {str(e)}")
            raise InternalErrorHTTPException()
