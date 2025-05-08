from src.repositories.base import BaseRepository
from src.models.mood_tracker import MoodTrackerOrm
from src.repositories.mappers.mappers import MoodTrackerDataMapper


class MoodTrackerRepository(BaseRepository):
    model = MoodTrackerOrm
    mapper = MoodTrackerDataMapper
