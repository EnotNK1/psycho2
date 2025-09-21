import uuid

from src.repositories.answer_choices import AnswerChoiceRepository
from src.repositories.borders import BordersRepository
from src.repositories.clients import ClientsRepository
from src.repositories.education_material import EducationRepository
from src.repositories.education_card import EducationCardRepository
from src.repositories.education_progress import EducationProgressRepository
from src.repositories.education_theme import EducationThemeRepository
from src.repositories.inquiry import InquiryRepository
from src.repositories.questions import QuestionRepository
from src.repositories.scale import ScalesRepository
from src.repositories.scale_result import ScaleResultRepository
from src.repositories.tasks import TasksRepository
from src.repositories.test_result import TestResultRepository
from src.repositories.tests import TestsRepository
from src.repositories.review import ReviewRepository
from src.repositories.users import UsersRepository
from src.repositories.diary import DiaryRepository
from src.repositories.mood_tracker import MoodTrackerRepository
from src.repositories.application import ApplicationRepository
from src.repositories.daily_tasks import DailyTasksRepository
from src.repositories.emoji import EmojiRepository


class DBManager:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()

        self.users = UsersRepository(self.session)
        self.tests = TestsRepository(self.session)
        self.scales = ScalesRepository(self.session)
        self.borders = BordersRepository(self.session)
        self.answer_choice = AnswerChoiceRepository(self.session)
        self.question = QuestionRepository(self.session)
        self.tasks = TasksRepository(self.session)
        self.clients = ClientsRepository(self.session)
        self.application = ApplicationRepository(self.session)
        self.inquiry = InquiryRepository(self.session)
        self.review = ReviewRepository(self.session)
        self.diary = DiaryRepository(self.session)
        self.mood_tracker = MoodTrackerRepository(self.session)
        self.test_result = TestResultRepository(self.session)
        self.scale_result = ScaleResultRepository(self.session)
        self.daily_tasks = DailyTasksRepository(self.session)
        self.emoji = EmojiRepository(self.session)

        # Education repositories
        self.education_material = EducationRepository(self.session)
        self.education_card = EducationCardRepository(self.session)
        self.education_progress = EducationProgressRepository(self.session)
        self.education_theme = EducationThemeRepository(self.session)
        return self

    async def __aexit__(self, *args):
        await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

    async def execute(self, query):
        return await self.session.execute(query)

    async def get(self, model, id: uuid.UUID):
        return await self.session.get(model, id)

    async def add(self, entity):
        self.session.add(entity)
