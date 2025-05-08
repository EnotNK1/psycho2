import uuid

from src.models.tests import AnswerChoiceOrm, QuestionOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import AnswerChoiceDataMapper
from src.repositories.tests import logger


class AnswerChoiceRepository(BaseRepository):
    model = AnswerChoiceOrm
    mapper_class = AnswerChoiceDataMapper

