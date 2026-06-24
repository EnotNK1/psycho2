from src.repositories.base import BaseRepository
from src.models.diary import AbcDiaryEntryOrm
from src.repositories.mappers.mappers import AbcDiaryDataMapper


class AbcDiaryRepository(BaseRepository):
    model = AbcDiaryEntryOrm
    mapper = AbcDiaryDataMapper