import asyncio
from datetime import datetime
from symtable import Class

from celery.worker.consumer import Tasks

from src.models import ScaleOrm, InquiryOrm
from src.models.application import ApplicationOrm
from src.models.clients import TasksOrm, ClientsOrm
from src.models.education import EducationProgressOrm, educationThemeOrm, educationMaterialOrm, CardOrm
from src.models.tests import TestOrm, QuestionOrm, AnswerChoiceOrm, ScaleResultOrm, BordersOrm, TestResultOrm
from src.repositories.mappers.base import DataMapper
from src.schemas.application import ApplicationResponse
from src.schemas.education_material import EducationThemeResponse, EducationMaterialResponse, CardResponse, \
    EducationProgressResponse
from src.schemas.inquiry import Inquiry
from src.schemas.task import TaskRequest, Task
from src.schemas.tests import Test, Scale, TestResult, Question, AnswerChoice, ScaleResult, Borders
from src.schemas.users import User, ClientSchema, GetAllManagerRequest, AdminUserResponse
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
            job_title=model.job_title,
            face_to_face=model.face_to_face,
            role_id=model.role_id
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


class AdminUserDataMapper(DataMapper):
    db_model = UsersOrm
    schema = AdminUserResponse

    @staticmethod
    def map_to_domain_entity(model) -> schema:
        return AdminUserResponse(
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
            job_title=model.job_title,
            face_to_face=model.face_to_face,
            role_id=model.role_id,
            created_at=model.created_at,
            updated_at=model.updated_at
        )


class CardDataMapper(DataMapper):
    db_model = CardOrm
    schema = CardResponse

    @staticmethod
    async def map_to_domain_entity(model: CardOrm) -> CardResponse:
        return CardResponse(
            id=model.id,
            text=model.text,
            number=model.number,
            link_to_picture=model.link_to_picture
        )



class EducationMaterialDataMapper(DataMapper):
    db_model = educationMaterialOrm
    schema = EducationMaterialResponse

    @staticmethod
    async def map_to_domain_entity(model: educationMaterialOrm) -> EducationMaterialResponse:
        cards = await asyncio.gather(
            *[CardDataMapper.map_to_domain_entity(card) for card in model.cards]
        )

        return EducationMaterialResponse(
            id=model.id,
            type=model.type,
            number=model.number,
            title=model.title,
            link_to_picture=model.link_to_picture,
            subtitle=model.subtitle,
            cards=cards
        )



class EducationThemeDataMapper(DataMapper):
    db_model = educationThemeOrm
    schema = EducationThemeResponse

    @staticmethod
    async def map_to_domain_entity(model: educationThemeOrm) -> EducationThemeResponse:
        education_materials = await asyncio.gather(
            *[EducationMaterialDataMapper.map_to_domain_entity(material) for material in model.education_materials]
        )

        return EducationThemeResponse(
            id=model.id,
            theme=model.theme,
            link=model.link,
            related_topics=model.related_topics,
            education_materials=education_materials
        )


class EducationProgressDataMapper(DataMapper):
    db_model = EducationProgressOrm
    schema = EducationProgressResponse

    @staticmethod
    def map_to_domain_entity(model: EducationProgressOrm) -> EducationProgressResponse:
        return EducationProgressResponse(
            id=model.id,
            user_id=model.user_id,
            education_material_id=model.education_material_id
        )