


from src.models.daily_tasks import DailyTaskOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import DailyTaskDataMapper


class DailyTasksRepository(BaseRepository):
    model = DailyTaskOrm
    mapper  = DailyTaskDataMapper
