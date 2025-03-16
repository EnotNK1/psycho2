import uuid

from sqlalchemy import select

from src.repositories.base import BaseRepository
from src.models.tests import BordersOrm
from src.repositories.mappers.mappers import BordersDataMapper

class BordersRepository(BaseRepository):
    model = BordersOrm
    mapper = BordersDataMapper

    async def all_by_scale_id(self, scale_id: uuid.UUID) -> list[BordersOrm]:
        return await self.get_all_by_filter(scale_id=scale_id)