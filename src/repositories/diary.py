import uuid

from sqlalchemy import select

from src.repositories.base import BaseRepository
from src.models.diary import DiaryOrm
from src.repositories.mappers.mappers import DiaryDataMapper


class DiaryRepository(BaseRepository):
    model = DiaryOrm
    mapper = DiaryDataMapper

    async def get_latest_by_mood_tracker(
        self, user_id: uuid.UUID, mood_tracker_id: uuid.UUID
    ):
        result = await self.session.execute(
            select(self.model)
            .where(self.model.user_id == user_id, self.model.mood_tracker_id == mood_tracker_id)
            .order_by(self.model.created_at.desc(), self.model.id.desc())
            .limit(1)
        )
        diary = result.scalars().first()
        return self.mapper.map_to_domain_entity(diary) if diary is not None else None
