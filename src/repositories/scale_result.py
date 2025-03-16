
import uuid
from sqlalchemy import select

from src.repositories.base import BaseRepository
from src.models.tests import ScaleResultOrm
from src.repositories.mappers.mappers import ScaleResultDataMapper

class ScaleResultRepository(BaseRepository):
    model = ScaleResultOrm
    mapper = ScaleResultDataMapper


    async def get_all_by_test_result_id(self, test_result_id: uuid.UUID) -> list[ScaleResultOrm]:
        return await self.get_all_by_filter(test_result_id=test_result_id)