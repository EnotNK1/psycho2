from datetime import datetime
from symtable import Class

from celery.worker.consumer import Tasks

from src.models import ScaleOrm, InquiryOrm
from src.models.application import ApplicationOrm
from src.models.clients import TasksOrm, ClientsOrm
from src.models.tests import TestOrm, QuestionOrm, AnswerChoiceOrm, ScaleResultOrm, BordersOrm, TestResultOrm
from src.repositories.mappers.base import DataMapper
from src.schemas.application import ApplicationResponse
from src.schemas.inquiry import Inquiry
from src.schemas.task import TaskRequest, Task
from src.schemas.tests import Test, Scale, TestResult, Question, AnswerChoice, ScaleResult, Borders
from src.schemas.users import User, ClientSchema, GetAllManagerRequest
from src.models.application import ApplicationOrm
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

    @staticmethod
    def map_to_domain_entity(model):
        return GetAllManagerRequest(
            id=model.id,
            username=model.username,
            email=model.email,
            city=model.city,
            company=model.company,
            online=model.online,
            gender=model.gender,
            birth_date=model.birth_date,
            phone_number=model.phone_number,
            description=model.description,
            is_active=model.is_active,
            department=model.department,
            face_to_face=model.face_to_face
        )


class TestDataMapper(DataMapper):
    db_model = TestOrm
    schema = Test

    @staticmethod
    def map_to_domain_entity(model) -> schema:
        # Преобразуем только простые поля, игнорируя асинхронные отношения
        return Test(
            id=model.id,
            title=model.title,
            description=model.description,
            short_desc=model.short_desc,
            link=model.link,
            # Игнорируем асинхронные отношения
            test_result=[],
            question=[],
            scale=[],
        )


class ScaleDataMapper(DataMapper):
    db_model = ScaleOrm
    schema = Scale

    @staticmethod
    def map_to_domain_entity(model) -> schema:
        return Scale(
            id=model.id,
            title=model.title,
            min=model.min,
            max=model.max,
            test_id=model.test_id,
            scale_result=[],  # По умолчанию пустой список
            borders=[],  # По умолчанию пустой список
        )


class BordersDataMapper(DataMapper):
    db_model = BordersOrm
    schema = Borders

    @staticmethod
    def map_to_domain_entity(model) -> schema:
        return Borders(
            id=model.id,
            left_border=model.left_border,
            right_border=model.right_border,
            color=model.color,
            title=model.title,
            user_recommendation=model.user_recommendation,
            scale_id=model.scale_id,
        )


class AnswerChoiceDataMapper(DataMapper):
    db_model = AnswerChoiceOrm
    schema = AnswerChoice

    @staticmethod
    def map_to_domain_entity(model: AnswerChoiceOrm) -> AnswerChoice:
        return AnswerChoice(
            id=model.id,
            text=model.text,
            score=model.score
        )


class QuestionDataMapper(DataMapper):
    db_model = QuestionOrm
    schema = Question
    @staticmethod
    def map_to_domain_entity(model: QuestionOrm) -> Question:
        return Question(
            id=model.id,
            text=model.text,
            number=model.number,
            test_id=model.test_id,
            answer_choice=model.answer_choice  # Список ID ответов
        )


class TestResultDataMapper(DataMapper):
    db_model = TestResultOrm
    schema = TestResult


class ScaleResultDataMapper(DataMapper):
    db_model = ScaleResultOrm
    schema = ScaleResult


class TasksDataMapper(DataMapper):
    db_model = TasksOrm
    schema = Task


class ClientsDataMapper(DataMapper):
    db_model = ClientsOrm
    schema = User

    @staticmethod
    def map_to_domain_entity(model) -> ClientSchema:
        return ClientSchema(
            id=model.id,
            client_id=model.client_id,
            mentor_id=model.mentor_id,
            text=model.text,
            status=model.status
        )


class ApplicationDataMapper(DataMapper):
    db_model = ApplicationOrm
    schema = ApplicationResponse

class InquiryDataMapper(DataMapper):
    db_model = InquiryOrm
    schema = Inquiry

class ReviewDataMapper(DataMapper):
    db_model = ReviewOrm
    schema = Review


class DiaryDataMapper(DataMapper):
    db_model = DiaryOrm
    schema = Diary


class MoodTrackerDataMapper(DataMapper):
    db_model = MoodTrackerOrm
    schema = MoodTracker