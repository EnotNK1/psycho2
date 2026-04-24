import uuid

import pytest
from sqlalchemy import select

import src.api.training_exercise as training_api_module
from autotest.factories.training_exercise import USER_ID
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.models.training_exercises import (
    TrainingCompletedExerciseOrm,
    TrainingExerciseOrm,
)
from src.models.users import UsersOrm
from src.services.fixtures.training_exercise import TRAINING_EXERCISES


SEEDED_EXERCISE_ID = uuid.UUID(TRAINING_EXERCISES[0]["id"])


def build_user_orm(*, user_id=USER_ID):
    return UsersOrm(
        id=user_id,
        email="training@example.com",
        username="trainer",
        hashed_password="hashed",
        city="Tomsk",
        company=None,
        online=None,
        gender="male",
        birth_date=__import__("datetime").date(1999, 1, 1),
        phone_number="+70000000001",
        description=None,
        role_id=1,
        is_active=True,
        department=None,
        job_title=None,
        face_to_face=None,
    )


@pytest.fixture
def training_integration_client_factory(api_client_factory, integration_db_manager_factory):
    def _factory(user_id=USER_ID):
        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                training_api_module.router,
                dependency_overrides={
                    get_db: integration_db_manager_factory,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client

        return _client()

    return _factory


async def fetch_completed_rows(session_factory):
    async with session_factory() as session:
        result = await session.execute(select(TrainingCompletedExerciseOrm))
        return result.scalars().all()


@pytest.mark.asyncio
async def test_training_exercise_seed_and_list_integration(
    training_integration_client_factory,
    integration_session_factory,
):
    async with integration_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    async for client in training_integration_client_factory():
        seed_response = await client.post("/training-exercises/auto-create")
        list_response = await client.get("/training-exercises/")

    assert seed_response.status_code == 200
    assert seed_response.json() == {"status": "ok"}
    assert list_response.status_code == 200
    body = list_response.json()
    assert "exercises" in body
    assert len(body["exercises"]) >= 3
    assert any(item["id"] == str(SEEDED_EXERCISE_ID) for item in body["exercises"])
    assert all(sorted(item.keys()) == ["id", "is_completed", "picture_link", "title"] for item in body["exercises"])

    async with integration_session_factory() as session:
        result = await session.execute(select(TrainingExerciseOrm))
        assert len(result.scalars().all()) >= 3


@pytest.mark.asyncio
async def test_training_exercise_detail_complete_and_completed_integration(
    training_integration_client_factory,
    integration_session_factory,
):
    async with integration_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    async for client in training_integration_client_factory():
        await client.post("/training-exercises/auto-create")
        before_response = await client.get(f"/training-exercises/{SEEDED_EXERCISE_ID}")
        complete_response = await client.post(f"/training-exercises/{SEEDED_EXERCISE_ID}/complete")
        completed_response = await client.get(f"/training-exercises/{SEEDED_EXERCISE_ID}/completed")
        after_response = await client.get(f"/training-exercises/{SEEDED_EXERCISE_ID}")

    assert before_response.status_code == 200
    assert before_response.json()["is_completed"] is False
    assert complete_response.status_code == 200
    assert complete_response.json() == {"status": "ok"}
    assert completed_response.status_code == 200
    assert completed_response.json() == {"is_completed": True}
    assert after_response.status_code == 200
    assert after_response.json()["is_completed"] is True

    rows = await fetch_completed_rows(integration_session_factory)
    assert len(rows) == 1
    assert rows[0].training_exercise_id == SEEDED_EXERCISE_ID
    assert rows[0].user_id == USER_ID


@pytest.mark.asyncio
async def test_training_exercise_structure_integration_returns_nested_questions_and_variants(
    training_integration_client_factory,
    integration_session_factory,
):
    async with integration_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    async for client in training_integration_client_factory():
        await client.post("/training-exercises/auto-create")
        response = await client.get(f"/training-exercises/{SEEDED_EXERCISE_ID}/structure")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(SEEDED_EXERCISE_ID)
    assert len(body["questions"]) > 0
    assert "variants" in body["questions"][0]
    assert len(body["questions"][0]["variants"]) > 1
    assert sorted(body["questions"][0]["variants"][0].keys()) == [
        "correct",
        "explanation",
        "id",
        "question_id",
        "title",
    ]


@pytest.mark.asyncio
async def test_training_exercise_detail_should_return_404_for_missing_entity(
    training_integration_client_factory,
):
    missing_id = uuid.uuid4()

    async for client in training_integration_client_factory():
        response = await client.get(f"/training-exercises/{missing_id}")

    assert response.status_code == 404
