import uuid
from ctypes import cast
from datetime import datetime, timedelta, date
from http.client import HTTPException
from sqlite3 import Date

from src.models.diary import DiaryOrm
from src.schemas.diary import Diary, DiaryRequestAdd, DiaryDateRequestAdd
from src.services.base import BaseService


class DiaryService(BaseService):
    async def add_diary(self, data: DiaryRequestAdd, user_id: uuid.UUID):
        # user = await self.db.users.get_one_or_none(id=user_id)
        diary = Diary(
            id=uuid.uuid4(),
            text=data.text,
            created_at=datetime.now(),
        )
        await self.db.diary.add(diary)
        await self.db.commit()

    async def get_diary(self):
        return await self.db.diary.get_all()


    async def add_diary_with_date(self, data: DiaryDateRequestAdd, user_id: uuid.UUID):

        newday=datetime.strptime(data.day, '%Y-%m-%d')
        diary = Diary(
            id=uuid.uuid4(),
            text=data.text,
            created_at=newday,
        )
        await self.db.diary.add(diary)
        await self.db.commit()


    async def get_diary_by_day(self, day: str):

        target_date = datetime.strptime(day, '%Y-%m-%d').date()
        return await self.db.diary.get_filtered_by_date(target_date)


    async def get_diary_for_month(self, timestamp: int) -> list[dict]:
        target_date = datetime.utcfromtimestamp(timestamp)
        year = target_date.year
        month = target_date.month
        return await self.db.diary.get_diary_for_month(year, month)



    # async def read_review(self, review_id: uuid.UUID):
    #     data = ReviewRead(is_read=True)
    #     await self.db.review.edit(data, exclude_unset=True, id=review_id)
    #     await self.db.commit()
    #
    # async def delete_review(self, review_id: uuid.UUID):
    #     await self.db.review.delete(id=review_id)
    #     await self.db.commit()