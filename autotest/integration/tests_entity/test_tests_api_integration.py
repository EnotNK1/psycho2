import datetime
import uuid

import pytest
from sqlalchemy import select

import src.api.tests as tests_api_module
import src.services.tests as tests_service_module
import src.repositories.questions as questions_repository_module
from autotest4.factories.tests_entity import (
    ANSWER_ID,
    QUESTION_ID,
    RESULT_ID,
    SCALE_ID,
    SECOND_ANSWER_ID,
    SECOND_QUESTION_ID,
    SECOND_RESULT_ID,
    SECOND_SCALE_ID,
    SECOND_TEST_ID,
    SECOND_USER_ID,
    TEST_ID,
    USER_ID,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
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


def build_user_orm(*, user_id=USER_ID, email="tests@example.com"):
    return UsersOrm(
        id=user_id,
        email=email,
        username=f"user-{str(user_id)[:8]}",
        hashed_password="hashed",
        city="Tomsk",
        company=None,
        online=None,
        gender="male",
        birth_date=datetime.date(1999, 1, 1),
        phone_number="+70000000003",
        description=None,
        role_id=1,
        is_active=True,
        department=None,
        job_title=None,
        face_to_face=None,
    )


def build_manual_test_bundle():
    test = DbTestOrm(
        id=TEST_ID,
        type=None,
        title="Burnout Test",
        description="Long description",
        short_desc="Short description",
        link="/images/test.png",
    )
    second_test = DbTestOrm(
        id=SECOND_TEST_ID,
        type=None,
        title="Stress Test",
        description="Second description",
        short_desc="Second short",
        link="/images/second.png",
    )
    scale = ScaleOrm(id=SCALE_ID, title="Scale A", min=0, max=10, test_id=TEST_ID)
    second_scale = ScaleOrm(id=SECOND_SCALE_ID, title="Scale B", min=0, max=10, test_id=SECOND_TEST_ID)
    border = BordersOrm(
        id=uuid.UUID("90909090-9090-9090-9090-909090909090"),
        left_border=0,
        right_border=10,
        color="#00AA00",
        title="Norm",
        user_recommendation="Take care",
        scale_id=SCALE_ID,
    )
    answer = AnswerChoiceOrm(id=ANSWER_ID, text="Never", score=0)
    second_answer = AnswerChoiceOrm(id=SECOND_ANSWER_ID, text="Sometimes", score=1)
    question = QuestionOrm(
        id=QUESTION_ID,
        text="Question text",
        opposite_text="Opposite text",
        number=1,
        test_id=TEST_ID,
        answer_choice=[str(ANSWER_ID), str(SECOND_ANSWER_ID)],
    )
    second_question = QuestionOrm(
        id=SECOND_QUESTION_ID,
        text="Second question",
        opposite_text=None,
        number=2,
        test_id=SECOND_TEST_ID,
        answer_choice=[str(ANSWER_ID)],
    )
    test_result = DbTestResultOrm(
        id=RESULT_ID,
        user_id=USER_ID,
        test_id=TEST_ID,
        date=datetime.datetime(2026, 4, 15, 10, 0, 0),
    )
    second_result = DbTestResultOrm(
        id=SECOND_RESULT_ID,
        user_id=SECOND_USER_ID,
        test_id=SECOND_TEST_ID,
        date=datetime.datetime(2026, 4, 15, 11, 0, 0),
    )
    scale_result = ScaleResultOrm(
        id=uuid.uuid4(),
        score=7,
        scale_id=SCALE_ID,
        test_result_id=RESULT_ID,
    )
    second_scale_result = ScaleResultOrm(
        id=uuid.uuid4(),
        score=6,
        scale_id=SECOND_SCALE_ID,
        test_result_id=SECOND_RESULT_ID,
    )
    return [
        test,
        second_test,
        scale,
        second_scale,
        border,
        answer,
        second_answer,
        question,
        second_question,
        test_result,
        second_result,
        scale_result,
        second_scale_result,
    ]


@pytest.fixture
def tests_entity_client_factory(api_client_factory, tests_entity_db_manager_factory):
    def _factory(user_id=USER_ID):
        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                tests_api_module.router,
                dependency_overrides={
                    get_db: tests_entity_db_manager_factory,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client

        return _client()

    return _factory


async def seed_bundle(session_factory, *, include_second_user=False):
    async with session_factory() as session:
        session.add(build_user_orm())
        if include_second_user:
            session.add(build_user_orm(user_id=SECOND_USER_ID, email="tests-second@example.com"))
        for item in build_manual_test_bundle():
            session.add(item)
        await session.commit()


@pytest.mark.asyncio
async def test_tests_auto_create_and_list_integration(
    monkeypatch,
    tests_entity_client_factory,
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

    async for client in tests_entity_client_factory():
        auto_response = await client.post("/tests/auto")
        list_response = await client.get("/tests")

    assert auto_response.status_code == 200
    assert auto_response.json() == {"status": "OK"}
    assert list_response.status_code == 200
    assert len(list_response.json()) > 0

    async with tests_entity_session_factory() as session:
        tests = (await session.execute(select(DbTestOrm))).scalars().all()
        assert len(tests) > 0


@pytest.mark.asyncio
async def test_tests_read_endpoints_integration_return_real_data(
    tests_entity_client_factory,
    tests_entity_session_factory,
):
    await seed_bundle(tests_entity_session_factory, include_second_user=True)

    async for client in tests_entity_client_factory():
        all_response = await client.get("/tests")
        detail_response = await client.get(f"/tests/{TEST_ID}")
        questions_response = await client.get(f"/tests/{TEST_ID}/questions")
        questions_answers_response = await client.get(f"/tests/{TEST_ID}/questions/answers")
        answers_response = await client.get(f"/tests/{TEST_ID}/questions/{QUESTION_ID}/answers/")
        results_response = await client.get(f"/tests/{TEST_ID}/results/")
        result_by_id_response = await client.get(f"/tests/test_result/{RESULT_ID}")

    assert all_response.status_code == 200
    assert len(all_response.json()) == 2
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == str(TEST_ID)
    assert questions_response.status_code == 200
    assert len(questions_response.json()) == 1
    assert questions_answers_response.status_code == 200
    assert len(questions_answers_response.json()[0]["answer_choices"]) == 2
    assert answers_response.status_code == 200
    assert len(answers_response.json()) == 2
    assert results_response.status_code == 200
    assert results_response.json()[0]["test_result_id"] == str(RESULT_ID)
    assert result_by_id_response.status_code == 200
    assert result_by_id_response.json()["test_result_id"] == str(RESULT_ID)


@pytest.mark.asyncio
async def test_tests_passed_by_user_should_return_real_summaries_integration(
    tests_entity_client_factory,
    tests_entity_session_factory,
):
    await seed_bundle(tests_entity_session_factory, include_second_user=True)

    async for client in tests_entity_client_factory():
        response = await client.get(f"/tests/passed/user/{USER_ID}")

    assert response.status_code == 200
    assert response.json()[0]["test_id"] == str(TEST_ID)


@pytest.mark.asyncio
async def test_tests_details_should_return_all_answers_integration(
    tests_entity_client_factory,
    tests_entity_session_factory,
):
    await seed_bundle(tests_entity_session_factory)

    async for client in tests_entity_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/details")

    assert response.status_code == 200
    assert len(response.json()["questions"][0]["answers"]) == 2


@pytest.mark.asyncio
async def test_tests_passed_for_current_user_should_return_404_when_user_has_no_results_integration(
    tests_entity_client_factory,
    tests_entity_session_factory,
):
    async with tests_entity_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    async for client in tests_entity_client_factory():
        response = await client.get("/tests/passed/user")

    assert response.status_code == 404
