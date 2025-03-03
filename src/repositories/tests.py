import uuid
import logging
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from src.models.tests import TestOrm, ScaleOrm, QuestionOrm, AnswerChoiceOrm, BordersOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import TestDataMapper

logger = logging.getLogger(__name__)

class TestsRepository(BaseRepository):
    model = TestOrm
    mapper = TestDataMapper

    async def get_one(self, test_id: uuid.UUID) -> Optional[TestOrm]:
        try:
            query = (
                select(TestOrm)
                .options(
                    # Eager load related scales and their borders
                    selectinload(TestOrm.scale).selectinload(ScaleOrm.borders)
                    # Eager load questions and their associated answer choices

                )
                .where(TestOrm.id == test_id)
            )
            result = await self.session.execute(query)
            test = result.scalars().first()

            if not test:
                logger.warning(f"Тест с id={test_id} не найден.")
                return None

            return test

        except SQLAlchemyError as ex:
            logger.error(f"Ошибка при получении теста: {ex}")
            return None
