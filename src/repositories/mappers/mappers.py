from symtable import Class

from src.models import ScaleOrm
from src.models.tests import TestOrm, QuestionOrm, AnswerChoiceOrm, ScaleResultOrm, BordersOrm, TestResultOrm
from src.repositories.mappers.base import DataMapper
from src.schemas.tests import Test, Scale, TestResult, Question, AnswerChoice, ScaleResult, Borders
from src.schemas.users import User
from src.models.users import UsersOrm


class UserDataMapper(DataMapper):
    db_model = UsersOrm
    schema = User


class TestDataMapper(DataMapper):
    db_model = TestOrm
    schema = Test

    def map_to_domain_entity(self, db_model) -> schema:
        # Преобразуем только простые поля, игнорируя асинхронные отношения
        return Test(
            id=db_model.id,
            title=db_model.title,
            description=db_model.description,
            short_desc=db_model.short_desc,
            link=db_model.link,
            # Игнорируем асинхронные отношения
            test_result=[],
            question=[],
            scale=[],
        )


class ScaleDataMapper(DataMapper):
    db_model = ScaleOrm
    schema = Scale

    def map_to_domain_entity(self, db_model) -> schema:
        return Scale(
            id=db_model.id,
            title=db_model.title,
            min=db_model.min,
            max=db_model.max,
            test_id=db_model.test_id,
            scale_result=[],  # По умолчанию пустой список
            borders=[],  # По умолчанию пустой список
        )


class BordersDataMapper(DataMapper):
    db_model = BordersOrm
    schema = Borders

    def map_to_domain_entity(self, db_model) -> schema:
        return Borders(
            id=db_model.id,
            left_border=db_model.left_border,
            right_border=db_model.right_border,
            color=db_model.color,
            title=db_model.title,
            user_recommendation=db_model.user_recommendation,
            scale_id=db_model.scale_id,
        )


class AnswerChoiceDataMapper(DataMapper):
    db_model = AnswerChoiceOrm
    schema = AnswerChoice

    def map_to_domain_entity(self, db_model: AnswerChoiceOrm) -> AnswerChoice:
        return AnswerChoice(
            id=db_model.id,
            text=db_model.text,
            score=db_model.score
        )


class QuestionDataMapper(DataMapper):
    db_model = QuestionOrm
    schema = Question

    def map_to_domain_entity(self, db_model: QuestionOrm) -> Question:
        return Question(
            id=db_model.id,
            text=db_model.text,
            number=db_model.number,
            test_id=db_model.test_id,
            answer_choice=db_model.answer_choice  # Список ID ответов
        )
