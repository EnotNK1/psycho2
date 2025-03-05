import uuid
from typing import Optional

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

    async def get_one_or_none(self, **filter_by) -> Optional[TestResultOrm]:
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)
        return result.scalars().one_or_none()

    async def get_all_by_user_id(self, user_id: uuid.UUID) -> list[TestResultOrm]:
        query = select(self.model).filter_by(user_id=user_id)
        result = await self.session.execute(query)
        return result.scalars().all()
