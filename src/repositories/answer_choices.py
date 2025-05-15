import uuid

from src.models.tests import AnswerChoiceOrm, QuestionOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import AnswerChoiceDataMapper


class AnswerChoiceRepository(BaseRepository):
    model = AnswerChoiceOrm
    mapper = AnswerChoiceDataMapper

