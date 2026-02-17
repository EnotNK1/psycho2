from src.models import UserTaskOrm
from src.repositories.base import BaseRepository
from src.models.mood_tracker import MoodTrackerOrm
from src.repositories.mappers.mappers import MoodTrackerDataMapper, UserTasksDataMapper


class UserTaskRepository(BaseRepository):
    model = UserTaskOrm
    mapper = UserTasksDataMapper
