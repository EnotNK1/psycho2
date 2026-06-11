import uuid

from sqlalchemy import delete, select
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

    async def get_orm_one_or_none(self, material_id: uuid.UUID):
        query = select(self.model).where(self.model.id == material_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def add_entity(self, entity: educationMaterialOrm):
        self.session.add(entity)

    async def delete_not_in(
        self,
        theme_id: uuid.UUID,
        material_ids: set[uuid.UUID],
    ):
        query = delete(self.model).where(
            self.model.education_theme_id == theme_id
        )
        if material_ids:
            query = query.where(self.model.id.not_in(material_ids))
        await self.session.execute(query)
