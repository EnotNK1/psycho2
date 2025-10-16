import uuid

from sqlalchemy import select

from src.repositories.base import BaseRepository
from src.models.tests import BordersOrm
from src.repositories.mappers.mappers import BordersDataMapper


class BordersRepository(BaseRepository):
    model = BordersOrm
    mapper = BordersDataMapper
