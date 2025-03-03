import uuid

from sqlalchemy import select

from src.repositories.base import BaseRepository
from src.models.tests import BordersOrm
from src.repositories.mappers.mappers import BordersDataMapper

class BordersRepository(BaseRepository):
    model = BordersOrm
    mapper = BordersDataMapper

    async def all_by_scale_id(self, scale_id: uuid.UUID) -> list[BordersOrm]:
        """
        Возвращает все границы, связанные со шкалой по её ID.
        """
        query = select(BordersOrm).where(BordersOrm.scale_id == scale_id)
        result = await self.session.execute(query)
        return result.scalars().all()