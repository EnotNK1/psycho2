from operator import and_

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import cast
from sqlalchemy.types import Date
from src.repositories.base import BaseRepository
from src.models.mood_tracker import MoodTrackerOrm
from src.repositories.mappers.mappers import MoodTrackerDataMapper
from datetime import datetime, date

class MoodTrackerRepository(BaseRepository):
    model = MoodTrackerOrm
    mapper = MoodTrackerDataMapper


    async def get_filtered_by_date_mt(self, target_date: date):
        if self.model is None:
            raise ValueError("Model is not defined in the repository")

        if not hasattr(self.model, 'created_at'):
            raise ValueError(f"Model {self.model.__name__} does not have 'created_at' attribute")

        query = select(self.model).where(func.date(self.model.created_at) == target_date)
        result = await self.session.execute(query)

        return [
            self.mapper.map_to_domain_entity(model) for model in result.scalars().all()
        ]