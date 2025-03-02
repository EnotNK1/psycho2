import uuid
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from src.models.tests import TestOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import TestDataMapper
from src.schemas.tests import Test, TestAdd


class TestsRepository(BaseRepository):
    model = TestOrm
    mapper = TestDataMapper

