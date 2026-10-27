from src.repositories.base import BaseRepository
from src.models.tests import ScaleResultOrm
from src.repositories.mappers.mappers import ScaleResultDataMapper


class ScaleResultRepository(BaseRepository):
    model = ScaleResultOrm
    mapper = ScaleResultDataMapper
