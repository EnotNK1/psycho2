import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.education import educationThemeOrm, educationMaterialOrm
from src.repositories.base import BaseRepository


from src.repositories.mappers.mappers import EducationThemeDataMapper


class EducationThemeRepository(BaseRepository):
    model = educationThemeOrm
    mapper = EducationThemeDataMapper

    async def get_all_with_materials(self):
        query = select(self.model).options(
            selectinload(self.model.education_materials)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_with_materials(self, theme_id: uuid.UUID):
        query = select(self.model).where(self.model.id == theme_id).options(
            selectinload(self.model.education_materials).selectinload(
                educationMaterialOrm.cards
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all_with_materials_and_cards(self):
        query = select(self.model).options(
            selectinload(self.model.education_materials).selectinload(
                educationMaterialOrm.cards
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()