from src.models.application import ApplicationOrm
from src.repositories.mappers.base import DataMapper
from src.schemas.application import (
    ApplicationShortResponse,
    ApplicationFullResponse
)
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


class ApplicationShortDataMapper(DataMapper):
    db_model = ApplicationOrm
    schema = ApplicationShortResponse

    def __init__(self, session):
        self.session = session

    def map_to_domain_entity(self, model):
        if hasattr(model, 'client') and model.client:
            username = model.client.username
        else:
            from src.repositories.users import UsersRepository
            users_repo = UsersRepository(self.session)

            import asyncio
            user = asyncio.run(users_repo.get_one_or_none(id=model.client_id))
            username = user.username if user else "Unknown"

        return self.schema(
            app_id=model.id,
            client_id=model.client_id,
            username=username,
            text=model.text,
            online=model.online,
            problem_id=model.problem_id,
            problem=model.problem
        )


class ApplicationFullDataMapper(DataMapper):
    db_model = ApplicationOrm
    schema = ApplicationFullResponse

    @classmethod
    def map_to_domain_entity(cls, model):
        return cls.schema(
            app_id=model.id,
            client_id=model.client_id,
            is_active=model.is_active,
            text=model.text
        )


