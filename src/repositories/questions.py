import uuid

from sqlalchemy import select

from src.models.tests import QuestionOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import QuestionDataMapper


class QuestionRepository(BaseRepository):
    model = QuestionOrm
    mapper = QuestionDataMapper

