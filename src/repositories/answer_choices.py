from src.repositories.base import BaseRepository
from src.models.tests import AnswerChoiceOrm
from src.repositories.mappers.mappers import AnswerChoiceDataMapper


class AnswerChoiceRepository(BaseRepository):
    model = AnswerChoiceOrm
    mapper = AnswerChoiceDataMapper