import uuid

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from src.models import ScaleOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import ScaleDataMapper
from src.schemas.tests import Scale, ScaleAdd


class ScalesRepository(BaseRepository):
    model = ScaleOrm
    mapper = ScaleDataMapper

    async def get_all_by_test_id(self, test_id: uuid.UUID) -> list[ScaleOrm]:
        """
        Возвращает все шкалы, связанные с тестом по его ID.
        """
        query = select(ScaleOrm).where(ScaleOrm.test_id == test_id)
        result = await self.session.execute(query)
        return result.scalars().all()