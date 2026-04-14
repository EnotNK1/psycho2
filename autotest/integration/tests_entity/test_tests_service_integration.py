import datetime
import uuid

import pytest
from sqlalchemy import select

import src.services.tests as tests_service_module
import src.repositories.questions as questions_repository_module
from autotest4.factories.tests_entity import (
    ANSWER_ID,
    QUESTION_ID,
    RESULT_ID,
    SCALE_ID,
    SECOND_ANSWER_ID,
    SECOND_TEST_ID,
    TEST_ID,
    USER_ID,
)
from src.exceptions import ObjectNotFoundException
from src.models.tests import (
    AnswerChoiceOrm,
    BordersOrm,
    QuestionOrm,
    ScaleOrm,
    ScaleResultOrm,
    TestOrm as DbTestOrm,
    TestResultOrm as DbTestResultOrm,
)
from src.models.users import UsersOrm
from src.services.tests import TestService as TestsSvc


class DummyInquiryService:
    def __init__(self, db):
        self.db = db

    async def check_and_create_inquiries(self, data):
        return None


class DummyEmojiService:
    def __init__(self, db):
        self.db = db

    async def check_and_create_emojis(self, data):
        return None


def build_user_orm():
    return UsersOrm(
        id=USER_ID,
        email="tests-service@example.com",
        username="tests-service",
        hashed_password="hashed",
        city="Tomsk",
        company=None,
        online=None,
        gender="male",
        birth_date=datetime.date(1999, 1, 1),
        phone_number="+70000000004",
        description=None,
        role_id=1,
        is_active=True,
        department=None,
        job_title=None,
        face_to_face=None,
    )


async def seed_manual_bundle(session_factory):
    async with session_factory() as session:
        session.add(build_user_orm())
        session.add(DbTestOrm(id=TEST_ID, type=None, title="Burnout Test", description="Long description", short_desc="Short", link="/images/test.png"))
        session.add(DbTestOrm(id=SECOND_TEST_ID, type=None, title="Stress Test", description="Second description", short_desc="Second", link="/images/second.png"))
        session.add(ScaleOrm(id=SCALE_ID, title="Scale A", min=0, max=10, test_id=TEST_ID))
        session.add(BordersOrm(id=uuid.UUID("12111111-2222-3333-4444-555555555555"), left_border=0, right_border=10, color="#00AA00", title="Norm", user_recommendation="Take care", scale_id=SCALE_ID))
        session.add(AnswerChoiceOrm(id=ANSWER_ID, text="Never", score=0))
        session.add(AnswerChoiceOrm(id=SECOND_ANSWER_ID, text="Sometimes", score=1))
        session.add(
            QuestionOrm(
                id=QUESTION_ID,
                text="Question text",
                opposite_text="Opposite text",
                number=1,
                test_id=TEST_ID,
                answer_choice=[str(ANSWER_ID), str(SECOND_ANSWER_ID)],
            )
        )
        session.add(DbTestResultOrm(id=RESULT_ID, user_id=USER_ID, test_id=TEST_ID, date=datetime.datetime(2026, 4, 15, 10, 0, 0)))
        session.add(ScaleResultOrm(id=uuid.uuid4(), score=7, scale_id=SCALE_ID, test_result_id=RESULT_ID))
        await session.commit()


@pytest.mark.asyncio
async def test_tests_service_auto_create_persists_real_rows_integration(
    monkeypatch,
    tests_entity_db,
    tests_entity_session_factory,
):
    async def patched_question_add(self, data):
        self.session.add(
            QuestionOrm(
                id=data.id,
                text=data.text,
                opposite_text=data.opposite_text,
                number=data.number,
                test_id=data.test_id,
                answer_choice=[str(item) for item in data.answer_choice],
            )
        )

    monkeypatch.setattr(tests_service_module, "InquiryService", DummyInquiryService)
    monkeypatch.setattr(tests_service_module, "EmojiService", DummyEmojiService)
    monkeypatch.setattr(questions_repository_module.QuestionRepository, "add", patched_question_add)

    await TestsSvc(tests_entity_db).auto_create()

    async with tests_entity_session_factory() as session:
        tests = (await session.execute(select(DbTestOrm))).scalars().all()
        questions = (await session.execute(select(QuestionOrm))).scalars().all()
        answers = (await session.execute(select(AnswerChoiceOrm))).scalars().all()

    assert len(tests) > 0
    assert len(questions) > 0
    assert len(answers) > 0


@pytest.mark.asyncio
async def test_tests_service_details_should_include_all_answers_from_real_db(
    tests_entity_db,
    tests_entity_session_factory,
):
    await seed_manual_bundle(tests_entity_session_factory)

    result = await TestsSvc(tests_entity_db).details(TEST_ID)

    assert len(result.questions[0].answers) == 2


@pytest.mark.asyncio
async def test_tests_service_get_passed_tests_by_user_returns_real_summaries(
    tests_entity_db,
    tests_entity_session_factory,
):
    await seed_manual_bundle(tests_entity_session_factory)

    result = await TestsSvc(tests_entity_db).get_passed_tests_by_user(USER_ID)

    assert result[0]["test_id"] == str(TEST_ID)
    assert result[0]["title"] == "Burnout Test"


@pytest.mark.asyncio
async def test_tests_service_get_test_result_by_id_returns_real_payload(
    tests_entity_db,
    tests_entity_session_factory,
):
    await seed_manual_bundle(tests_entity_session_factory)

    result = await TestsSvc(tests_entity_db).get_test_result_by_id(RESULT_ID)

    assert result["test_result_id"] == str(RESULT_ID)
    assert result["scale_results"][0]["score"] == 7


@pytest.mark.asyncio
async def test_tests_service_get_passed_tests_by_user_raises_not_found_for_empty_history(
    tests_entity_db,
):
    with pytest.raises(ObjectNotFoundException):
        await TestsSvc(tests_entity_db).get_passed_tests_by_user(USER_ID)
