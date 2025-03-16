import uuid

from sqlalchemy import select

from src.models.tests import QuestionOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import QuestionDataMapper


class QuestionRepository(BaseRepository):
    model = QuestionOrm
    mapper = QuestionDataMapper

    async def all_by_test_id(self, test_id: uuid.UUID) -> list[QuestionOrm]:
        return await self.get_all_by_filter(test_id=test_id)
