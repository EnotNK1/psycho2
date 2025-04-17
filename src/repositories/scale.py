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

