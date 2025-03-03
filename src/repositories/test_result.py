import uuid
from sqlalchemy import select

from src.repositories.base import BaseRepository
from src.models.tests import TestResultOrm
from src.repositories.mappers.mappers import TestResultDataMapper

class TestResultRepository(BaseRepository):
    model = TestResultOrm
    mapper = TestResultDataMapper

    async def add_test_result(self, test_result: TestResultOrm):
        self.session.add(test_result)
        await self.session.commit()