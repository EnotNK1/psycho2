
import uuid
from sqlalchemy import select

from src.repositories.base import BaseRepository
from src.models.tests import ScaleResultOrm
from src.repositories.mappers.mappers import ScaleResultDataMapper

class ScaleResultRepository(BaseRepository):
    model = ScaleResultOrm
    mapper = ScaleResultDataMapper

    async def add_scale_result(self, scale_result: ScaleResultOrm):
        self.session.add(scale_result)  # Используем session.add для ORM-объекта
        await self.session.commit()
