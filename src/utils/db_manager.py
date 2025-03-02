from src.repositories.answer_choices import AnswerChoiceRepository
from src.repositories.borders import BordersRepository
from src.repositories.questions import QuestionRepository
from src.repositories.scale import ScalesRepository
from src.repositories.tests import TestsRepository
from src.repositories.users import UsersRepository
from src.schemas.tests import AnswerChoice, Question


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

        return self

    async def __aexit__(self, *args):
        await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()