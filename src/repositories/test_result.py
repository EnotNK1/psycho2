import uuid
from typing import Optional

from sqlalchemy import select

from src.repositories.base import BaseRepository
from src.models.tests import TestResultOrm
from src.repositories.mappers.mappers import TestResultDataMapper


class TestResultRepository(BaseRepository):
    model = TestResultOrm
    mapper = TestResultDataMapper



