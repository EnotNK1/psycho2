import uuid
from typing import Optional

from sqlalchemy import select

from src.repositories.base import BaseRepository
from src.models.tests import TestResultOrm
from src.repositories.mappers.mappers import TestResultDataMapper


class TestResultRepository(BaseRepository):
    model = TestResultOrm
    mapper = TestResultDataMapper


    async def get_all_by_user_id(self, user_id: uuid.UUID) -> list[TestResultOrm]:
        return await self.get_all_by_filter(user_id=user_id)
