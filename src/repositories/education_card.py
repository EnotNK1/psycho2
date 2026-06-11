import uuid
from typing import List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.education import CardOrm
from src.repositories.base import BaseRepository

from src.repositories.mappers.mappers import CardDataMapper


class EducationCardRepository(BaseRepository):
    model = CardOrm
    mapper  = CardDataMapper

    async def get_orm_one_or_none(self, card_id: uuid.UUID):
        query = select(self.model).where(self.model.id == card_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def add_entity(self, entity: CardOrm):
        self.session.add(entity)

    async def delete_not_in(
        self,
        material_id: uuid.UUID,
        card_ids: set[uuid.UUID],
    ):
        query = delete(self.model).where(
            self.model.education_material_id == material_id
        )
        if card_ids:
            query = query.where(self.model.id.not_in(card_ids))
        await self.session.execute(query)
