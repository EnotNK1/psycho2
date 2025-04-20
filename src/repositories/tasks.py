from src.models.clients import TasksOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import TasksDataMapper


class TasksRepository(BaseRepository):
    model = TasksOrm
    mapper = TasksDataMapper
