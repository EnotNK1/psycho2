from operator import and_

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import cast
from sqlalchemy.types import Date
from src.repositories.base import BaseRepository
from src.models.diary import DiaryOrm
from src.repositories.mappers.mappers import DiaryDataMapper
from datetime import datetime, date, timedelta


class DiaryRepository(BaseRepository):
    model = DiaryOrm
    mapper = DiaryDataMapper


    async def get_filtered_by_date(self, target_date: date):
        if self.model is None:
            raise ValueError("Model is not defined in the repository")

        if not hasattr(self.model, 'created_at'):
            raise ValueError(f"Model {self.model.__name__} does not have 'created_at' attribute")

        query = select(self.model).where(func.date(self.model.created_at) == target_date)
        result = await self.session.execute(query)

        return [
            self.mapper.map_to_domain_entity(model) for model in result.scalars().all()
        ]

    async def get_diary_for_month(self, year: int, month: int) -> list[dict]:
        result = []
        start_date = date(year, month, 1)
        next_month = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
        end_date = next_month - timedelta(days=1)

        current_date = start_date
        while current_date <= end_date:
            has_diary = await self.has_diary_on_date(current_date)
            result.append({
                "date": int(datetime(current_date.year, current_date.month, current_date.day).timestamp()),
                "diary": has_diary
            })
            current_date += timedelta(days=1)

        return result