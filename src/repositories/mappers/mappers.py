from src.repositories.mappers.base import DataMapper
from src.schemas.users import User
from src.schemas.review import Review
from src.schemas.diary import Diary
from src.schemas.mood_tracker import MoodTracker
from src.models.users import UsersOrm
from src.models.review import ReviewOrm
from src.models.diary import DiaryOrm
from src.models.mood_tracker import MoodTrackerOrm


class UserDataMapper(DataMapper):
    db_model = UsersOrm
    schema = User


class ReviewDataMapper(DataMapper):
    db_model = ReviewOrm
    schema = Review


class DiaryDataMapper(DataMapper):
    db_model = DiaryOrm
    schema = Diary


class MoodTrackerDataMapper(DataMapper):
    db_model = MoodTrackerOrm
    schema = MoodTracker


