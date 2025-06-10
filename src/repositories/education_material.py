import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.exceptions import ObjectNotFoundException
from src.models.education import educationMaterialOrm
from src.repositories.base import BaseRepository

from src.repositories.mappers.mappers import EducationMaterialDataMapper


class EducationRepository(BaseRepository):
    model = educationMaterialOrm
    mapper  = EducationMaterialDataMapper

    async def get_with_cards(self, material_id: uuid.UUID):
        query = select(self.model).where(
            self.model.id == material_id
        ).options(
            selectinload(self.model.cards)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_with_cards_or_raise(self, material_id: uuid.UUID):
        query = select(self.model).where(self.model.id == material_id).options(
            selectinload(self.model.cards)
        )
        result = await self.session.execute(query)
        obj = result.scalars().first()
        if obj is None:
            raise ObjectNotFoundException
        return self.mapper.map_to_domain_entity(obj)
