from src.repositories.base import BaseRepository
from src.models.diary import DiaryOrm
from src.repositories.mappers.mappers import DiaryDataMapper


class DiaryRepository(BaseRepository):
    model = DiaryOrm
    mapper = DiaryDataMapper
