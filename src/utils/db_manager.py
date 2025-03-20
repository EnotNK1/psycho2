from src.repositories.review import ReviewRepository
from src.repositories.users import UsersRepository
from src.repositories.diary import DiaryRepository
from src.repositories.mood_tracker import MoodTrackerRepository


class DBManager:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()

        self.users = UsersRepository(self.session)
        self.review = ReviewRepository(self.session)
        self.diary = DiaryRepository(self.session)
        self.mood_tracker = MoodTrackerRepository(self.session)

        return self

    async def __aexit__(self, *args):
        await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()
