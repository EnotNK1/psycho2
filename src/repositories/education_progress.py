import uuid
from typing import Optional, List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.education import EducationProgressOrm
from src.repositories.base import BaseRepository

from src.repositories.mappers.mappers import EducationProgressDataMapper


class EducationProgressRepository(BaseRepository):
    model = EducationProgressOrm
    mapper = EducationProgressDataMapper