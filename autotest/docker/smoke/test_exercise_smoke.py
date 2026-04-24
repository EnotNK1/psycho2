import pytest

import src.api.exercise as exercise_api_module
from autotest.factories.exercise import (
    EXERCISE_ID,
    FIELD_ID,
    RESULT_ID,
    USER_ID,
    VARIANT_ID,
    VIEW_ID,
    build_complete_payload,
    build_completed_response,
    build_exercise_detail_response,
    build_exercise_payload,
    build_exercise_response,
    build_field_payload,
    build_field_response,
    build_result_detail_response,
    build_results_response,
    build_structure_response,
    build_variant_payload,
    build_variant_response,
    build_view_payload,
    build_view_response,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id


class DummyExerciseSmokeService:
    def __init__(self, db):
        self.db = db

    async def auto_create(self):
        return None

    async def get_all_exercises(self, user_id):
        return [build_exercise_response()]

    async def create_exercise(self, exercise_data):
        return build_exercise_response()

    async def delete_exercise(self, exercise_id):
        return None

    async def get_exercise_by_id(self, exercise_id, user_id):
        return build_exercise_detail_response()

    async def create_field(self, exercise_id, field_data):
        return build_field_response()

    async def delete_field(self, field_id):
        return None

    async def create_variant(self, field_id, variant_data):
        return build_variant_response()

    async def delete_variant(self, variant_id):
        return None

    async def create_exercise_view(self, exercise_id, view_data):
        return build_view_response()

    async def delete_exercise_view(self, view_id):
        return None

    async def get_exercise_structure_by_id(self, exercise_id, user_id):
        return build_structure_response()

    async def get_exercise_results(self, exercise_id, user_id):
        return build_results_response()

    async def get_exercise_result_detail(self, exercise_id, result_id, user_id):
        return build_result_detail_response()

    async def complete_exercise(self, user_id, completed_data):
        return build_completed_response()


@pytest.fixture
async def client(api_client_factory, monkeypatch):
    monkeypatch.setattr(exercise_api_module, "ExerciseService", DummyExerciseSmokeService)

    async def override_get_db():
        yield object()

    def override_get_current_user_id():
        return USER_ID

    async for async_client, _ in api_client_factory(
        exercise_api_module.router,
        dependency_overrides={
            get_db: override_get_db,
            get_current_user_id: override_get_current_user_id,
        },
    ):
        yield async_client


@pytest.mark.asyncio
async def test_exercise_auto_smoke(client):
    response = await client.post("/exercises/auto")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


@pytest.mark.asyncio
async def test_exercise_list_smoke(client):
    response = await client.get("/exercises/")
    assert response.status_code == 200
    assert response.json()["exercises"][0]["id"] == str(EXERCISE_ID)


@pytest.mark.asyncio
async def test_exercise_create_and_delete_smoke(client):
    create_response = await client.post("/exercises/", json=build_exercise_payload())
    delete_response = await client.delete(f"/exercises/{EXERCISE_ID}")
    assert create_response.status_code == 201
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_exercise_detail_smoke(client):
    response = await client.get(f"/exercises/{EXERCISE_ID}")
    assert response.status_code == 200
    assert response.json()["title"] == "Free writing"


@pytest.mark.asyncio
async def test_exercise_field_crud_smoke(client):
    create_response = await client.post(f"/exercises/{EXERCISE_ID}/fields/", json=build_field_payload())
    delete_response = await client.delete(f"/exercises/fields/{FIELD_ID}")
    assert create_response.status_code == 201
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_exercise_variant_crud_smoke(client):
    create_response = await client.post(f"/exercises/fields/{FIELD_ID}/variants/", json=build_variant_payload())
    delete_response = await client.delete(f"/exercises/variants/{VARIANT_ID}")
    assert create_response.status_code == 201
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_exercise_view_crud_smoke(client):
    create_response = await client.post(f"/exercises/{EXERCISE_ID}/views/", json=build_view_payload())
    delete_response = await client.delete(f"/exercises/views/{VIEW_ID}")
    assert create_response.status_code == 201
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_exercise_structure_smoke(client):
    response = await client.get(f"/exercises/{EXERCISE_ID}/structure")
    assert response.status_code == 200
    assert response.json()["pages"][0]["sections"][0]["id"] == str(FIELD_ID)


@pytest.mark.asyncio
async def test_exercise_results_smoke(client):
    response = await client.get(f"/exercises/{EXERCISE_ID}/results")
    assert response.status_code == 200
    assert response.json()["results"][0]["id"] == str(RESULT_ID)


@pytest.mark.asyncio
async def test_exercise_result_detail_smoke(client):
    response = await client.get(f"/exercises/{EXERCISE_ID}/results/{RESULT_ID}")
    assert response.status_code == 200
    assert response.json()["id"] == str(RESULT_ID)


@pytest.mark.asyncio
async def test_exercise_complete_smoke(client):
    response = await client.post("/exercises/complete", json=build_complete_payload())
    assert response.status_code == 201
    assert response.json()["id"] == str(RESULT_ID)
