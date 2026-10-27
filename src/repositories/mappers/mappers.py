from src.models import ScaleOrm, InquiryOrm
from src.models.application import ApplicationOrm
from src.models.tests import (
    TestOrm,
    QuestionOrm,
    AnswerChoiceOrm,
    ScaleResultOrm,
    BordersOrm,
    TestResultOrm,
)
from src.repositories.mappers.base import DataMapper
from src.schemas.application import ApplicationResponse
from src.schemas.inquiry import Inquiry
from src.schemas.tests import (
    Test,
    Scale,
    TestResult,
    Question,
    AnswerChoice,
    ScaleResult,
    Borders,
)
from src.schemas.users import User, GetAllManagerRequest
from src.models.application import ApplicationOrm
from src.repositories.mappers.base import DataMapper
from src.schemas.users import User
from src.models.users import UsersOrm
from src.models.clients import ClientsOrm
from src.schemas.users import ClientSchema


class ClientsDataMapper(DataMapper):
    db_model = ClientsOrm
    schema = ClientSchema


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
            higher_education_university=model.higher_education_university,
            higher_education_specialization=model.higher_education_specialization,
            academic_degree=model.academic_degree,
            courses=model.courses,
            work_format=model.work_format,
            association=model.association,
            avatar_link=model.avatar_link,
            role_id=model.role_id,
        )


class TestDataMapper(DataMapper):
    db_model = TestOrm
    schema = Test

    @staticmethod
    def map_to_domain_entity(model) -> schema:
        return Test(
            id=model.id,
            title=model.title,
            type=model.type,
            description=model.description,
            short_desc=model.short_desc,
            link=model.link,
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
            position=model.position,
            min=model.min,
            max=model.max,
            test_id=model.test_id,
            scale_result=[],
            borders=[],
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
        return AnswerChoice(id=model.id, text=model.text, score=model.score)


class QuestionDataMapper(DataMapper):
    db_model = QuestionOrm
    schema = Question

    @staticmethod
    def map_to_domain_entity(model: QuestionOrm) -> Question:
        return Question(
            id=model.id,
            text=model.text,
            opposite_text=model.opposite_text,
            number=model.number,
            test_id=model.test_id,
            answer_choice=model.answer_choice,
        )


class TestResultDataMapper(DataMapper):
    db_model = TestResultOrm
    schema = TestResult


class ScaleResultDataMapper(DataMapper):
    db_model = ScaleResultOrm
    schema = ScaleResult


class ApplicationDataMapper(DataMapper):
    db_model = ApplicationOrm
    schema = ApplicationResponse


class InquiryDataMapper(DataMapper):
    db_model = InquiryOrm
    schema = Inquiry

    @classmethod
    def map_to_domain_entity(cls, model: InquiryOrm) -> Inquiry:
        return cls.schema.model_validate(model, from_attributes=True)

    @classmethod
    def map_to_db_model(cls, schema: Inquiry) -> InquiryOrm:
        return cls.db_model(**schema.model_dump())
