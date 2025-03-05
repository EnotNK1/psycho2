
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

    async def get_all_by_test_result_id(self, test_result_id: uuid.UUID) -> list[ScaleResultOrm]:
        query = select(self.model).where(self.model.test_result_id == test_result_id)
        result = await self.session.execute(query)
        return result.scalars().all()