import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.education import CardOrm
from src.repositories.base import BaseRepository

from src.repositories.mappers.mappers import CardDataMapper


class EducationCardRepository(BaseRepository):
    model = CardOrm
    mapper  = CardDataMapper