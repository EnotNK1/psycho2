from src.models.exercise import FieldOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import FieldMapper


class FieldsRepository(BaseRepository):
    model = FieldOrm
    mapper = FieldMapper
