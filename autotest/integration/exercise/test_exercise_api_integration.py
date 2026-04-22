import datetime
import uuid

import pytest
from sqlalchemy import select

import src.api.exercise as exercise_api_module
from autotest.factories.exercise import (
    FIELD_ID,
    USER_ID,
    build_complete_payload,
    build_exercise_payload,
    build_field_payload,
    build_variant_payload,
    build_view_payload,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.models.exercise import CompletedExerciseOrm, ExerciseStructureOrm
from src.models.users import UsersOrm


def build_user_orm(*, user_id=USER_ID):
    return UsersOrm(
        id=user_id,
        email="exercise@example.com",
        username="exercise-user",
        hashed_password="hashed",
        city="Tomsk",
        company=None,
        online=None,
        gender="male",
        birth_date=datetime.date(1999, 1, 1),
        phone_number="+70000000101",
        description=None,
        role_id=1,
        is_active=True,
        department=None,
        job_title=None,
        face_to_face=None,
    )


@pytest.fixture
def exercise_integration_client_factory(api_client_factory, exercise_db_manager_factory):
    def _factory(user_id=USER_ID):
        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                exercise_api_module.router,
                dependency_overrides={
                    get_db: exercise_db_manager_factory,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client

        return _client()

    return _factory


@pytest.mark.asyncio
async def test_exercise_api_create_list_detail_and_delete_integration(
    exercise_integration_client_factory,
    exercise_session_factory,
):
    async with exercise_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    async for client in exercise_integration_client_factory():
        create_response = await client.post("/exercises/", json=build_exercise_payload())
        exercise_id = create_response.json()["id"]
        list_response = await client.get("/exercises/")
        detail_response = await client.get(f"/exercises/{exercise_id}")
        delete_response = await client.delete(f"/exercises/{exercise_id}")
        after_delete_response = await client.get(f"/exercises/{exercise_id}")

    assert create_response.status_code == 201
    assert list_response.status_code == 200
    assert any(item["id"] == exercise_id for item in list_response.json()["exercises"])
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Free writing"
    assert delete_response.status_code == 204
    assert after_delete_response.status_code == 404

    async with exercise_session_factory() as session:
        rows = (await session.execute(select(ExerciseStructureOrm))).scalars().all()
    assert rows == []


@pytest.mark.asyncio
async def test_exercise_api_field_variant_view_complete_and_results_integration(
    exercise_integration_client_factory,
    exercise_session_factory,
):
    async with exercise_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    async for client in exercise_integration_client_factory():
        create_response = await client.post("/exercises/", json=build_exercise_payload())
        exercise_id = create_response.json()["id"]
        field_response = await client.post(f"/exercises/{exercise_id}/fields/", json=build_field_payload(exercises=None))
        field_id = field_response.json()["id"]
        variant_response = await client.post(f"/exercises/fields/{field_id}/variants/", json=build_variant_payload())
        view_response = await client.post(f"/exercises/{exercise_id}/views/", json=build_view_payload())
        complete_response = await client.post(
            "/exercises/complete",
            json=build_complete_payload(
                exercise_structure_id=exercise_id,
                filled_fields=[{"field_id": field_id, "text": "Real answer"}],
            ),
        )
        results_response = await client.get(f"/exercises/{exercise_id}/results")
        result_id = results_response.json()["results"][0]["id"]
        detail_response = await client.get(f"/exercises/{exercise_id}/results/{result_id}")

    assert field_response.status_code == 201
    assert field_response.json()["exercise_structure_id"] == exercise_id
    assert variant_response.status_code == 201
    assert variant_response.json()["field_id"] == field_id
    assert view_response.status_code == 201
    assert complete_response.status_code == 201
    assert complete_response.json()["score"] == 10
    assert results_response.status_code == 200
    assert results_response.json()["results"][0]["preview"] == "Real answer"
    assert detail_response.status_code == 200
    assert detail_response.json()["sections"][0]["value"] == "Real answer"

    async with exercise_session_factory() as session:
        rows = (await session.execute(select(CompletedExerciseOrm))).scalars().all()
    assert len(rows) == 1
    assert rows[0].user_id == USER_ID


@pytest.mark.asyncio
async def test_exercise_api_missing_entities_return_expected_statuses_integration(
    exercise_integration_client_factory,
):
    missing_id = uuid.uuid4()

    async for client in exercise_integration_client_factory():
        detail_response = await client.get(f"/exercises/{missing_id}")
        delete_response = await client.delete(f"/exercises/{missing_id}")
        create_field_response = await client.post(f"/exercises/{missing_id}/fields/", json=build_field_payload())
        result_detail_response = await client.get(f"/exercises/{missing_id}/results/{uuid.uuid4()}")
        complete_response = await client.post(
            "/exercises/complete",
            json=build_complete_payload(exercise_structure_id=str(missing_id)),
        )

    assert detail_response.status_code == 404
    assert delete_response.status_code == 404
    assert create_field_response.status_code == 404
    assert result_detail_response.status_code == 404
    assert complete_response.status_code == 400


@pytest.mark.asyncio
async def test_exercise_api_delete_nested_resources_integration(
    exercise_integration_client_factory,
    exercise_session_factory,
):
    async with exercise_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    async for client in exercise_integration_client_factory():
        create_response = await client.post("/exercises/", json=build_exercise_payload())
        exercise_id = create_response.json()["id"]
        field_response = await client.post(f"/exercises/{exercise_id}/fields/", json=build_field_payload(exercises=None))
        field_id = field_response.json()["id"]
        variant_response = await client.post(f"/exercises/fields/{field_id}/variants/", json=build_variant_payload())
        variant_id = variant_response.json()["id"]
        view_response = await client.post(f"/exercises/{exercise_id}/views/", json=build_view_payload())

        delete_variant_response = await client.delete(f"/exercises/variants/{variant_id}")
        delete_field_response = await client.delete(f"/exercises/fields/{field_id}")
        delete_view_response = await client.delete(f"/exercises/views/{view_response.json().get('id', uuid.uuid4())}")

    assert delete_variant_response.status_code == 204
    assert delete_field_response.status_code == 204
    # ExerciseViewResponse does not expose id, so this assertion currently documents the API gap.
    assert delete_view_response.status_code == 404


@pytest.mark.asyncio
async def test_exercise_api_validates_uuid_and_payload_integration(exercise_integration_client_factory):
    async for client in exercise_integration_client_factory():
        invalid_uuid_response = await client.get("/exercises/not-a-uuid")
        invalid_create_response = await client.post("/exercises/", json={})
        invalid_complete_response = await client.post("/exercises/complete", json={})

    assert invalid_uuid_response.status_code == 422
    assert invalid_create_response.status_code == 422
    assert invalid_complete_response.status_code == 422
