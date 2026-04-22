import pytest
from fastapi import HTTPException

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


class DummyExerciseApiService:
    auto_called = False
    last_init_db = None
    last_create_payload = None
    last_exercise_id = None
    last_field_id = None
    last_variant_id = None
    last_view_id = None
    last_user_id = None
    last_complete_args = None

    create_response = build_exercise_response()
    field_response = build_field_response()
    variant_response = build_variant_response()
    view_response = build_view_response()
    list_response = [build_exercise_response()]
    detail_response = build_exercise_detail_response()
    structure_response = build_structure_response()
    results_response = build_results_response()
    result_detail_response = build_result_detail_response()
    completed_response = build_completed_response()

    raise_on = {}

    def __init__(self, db):
        self.db = db
        type(self).last_init_db = db

    @classmethod
    def reset(cls):
        cls.auto_called = False
        cls.last_init_db = None
        cls.last_create_payload = None
        cls.last_exercise_id = None
        cls.last_field_id = None
        cls.last_variant_id = None
        cls.last_view_id = None
        cls.last_user_id = None
        cls.last_complete_args = None
        cls.create_response = build_exercise_response()
        cls.field_response = build_field_response()
        cls.variant_response = build_variant_response()
        cls.view_response = build_view_response()
        cls.list_response = [build_exercise_response()]
        cls.detail_response = build_exercise_detail_response()
        cls.structure_response = build_structure_response()
        cls.results_response = build_results_response()
        cls.result_detail_response = build_result_detail_response()
        cls.completed_response = build_completed_response()
        cls.raise_on = {}

    @classmethod
    def _maybe_raise(cls, method):
        error = cls.raise_on.get(method)
        if error:
            raise error

    async def auto_create(self):
        self._maybe_raise("auto_create")
        type(self).auto_called = True

    async def create_exercise(self, exercise_data):
        self._maybe_raise("create_exercise")
        type(self).last_create_payload = exercise_data
        return type(self).create_response

    async def delete_exercise(self, exercise_id):
        self._maybe_raise("delete_exercise")
        type(self).last_exercise_id = exercise_id

    async def create_field(self, exercise_id, field_data):
        self._maybe_raise("create_field")
        type(self).last_exercise_id = exercise_id
        type(self).last_create_payload = field_data
        return type(self).field_response

    async def delete_field(self, field_id):
        self._maybe_raise("delete_field")
        type(self).last_field_id = field_id

    async def create_variant(self, field_id, variant_data):
        self._maybe_raise("create_variant")
        type(self).last_field_id = field_id
        type(self).last_create_payload = variant_data
        return type(self).variant_response

    async def delete_variant(self, variant_id):
        self._maybe_raise("delete_variant")
        type(self).last_variant_id = variant_id

    async def create_exercise_view(self, exercise_id, view_data):
        self._maybe_raise("create_exercise_view")
        type(self).last_exercise_id = exercise_id
        type(self).last_create_payload = view_data
        return type(self).view_response

    async def delete_exercise_view(self, view_id):
        self._maybe_raise("delete_exercise_view")
        type(self).last_view_id = view_id

    async def get_all_exercises(self, user_id):
        self._maybe_raise("get_all_exercises")
        type(self).last_user_id = user_id
        return type(self).list_response

    async def get_exercise_by_id(self, exercise_id, user_id):
        self._maybe_raise("get_exercise_by_id")
        type(self).last_exercise_id = exercise_id
        type(self).last_user_id = user_id
        return type(self).detail_response

    async def get_exercise_structure_by_id(self, exercise_id, user_id):
        self._maybe_raise("get_exercise_structure_by_id")
        type(self).last_exercise_id = exercise_id
        type(self).last_user_id = user_id
        return type(self).structure_response

    async def get_exercise_results(self, exercise_id, user_id):
        self._maybe_raise("get_exercise_results")
        type(self).last_exercise_id = exercise_id
        type(self).last_user_id = user_id
        return type(self).results_response

    async def get_exercise_result_detail(self, exercise_id, result_id, user_id):
        self._maybe_raise("get_exercise_result_detail")
        type(self).last_exercise_id = exercise_id
        type(self).last_create_payload = result_id
        type(self).last_user_id = user_id
        return type(self).result_detail_response

    async def complete_exercise(self, user_id, completed_data):
        self._maybe_raise("complete_exercise")
        type(self).last_complete_args = (user_id, completed_data)
        return type(self).completed_response


@pytest.fixture
def exercise_api_client_factory(api_client_factory, monkeypatch):
    DummyExerciseApiService.reset()
    monkeypatch.setattr(exercise_api_module, "ExerciseService", DummyExerciseApiService)

    def _factory(user_id=USER_ID):
        fake_db = object()

        async def override_get_db():
            yield fake_db

        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                exercise_api_module.router,
                dependency_overrides={
                    get_db: override_get_db,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client, fake_db

        return _client()

    return _factory


@pytest.mark.asyncio
async def test_auto_create_exercises_returns_ok(exercise_api_client_factory):
    async for client, fake_db in exercise_api_client_factory():
        response = await client.post("/exercises/auto")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    assert DummyExerciseApiService.auto_called is True
    assert DummyExerciseApiService.last_init_db is fake_db


@pytest.mark.asyncio
async def test_auto_create_exercises_returns_500_on_unexpected_error(exercise_api_client_factory):
    DummyExerciseApiService.raise_on["auto_create"] = RuntimeError("boom")
    async for client, _ in exercise_api_client_factory():
        response = await client.post("/exercises/auto")
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_all_exercises_returns_wrapped_list(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.get("/exercises/")
    assert response.status_code == 200
    assert response.json() == {"exercises": [build_exercise_response()]}
    assert DummyExerciseApiService.last_user_id == USER_ID


@pytest.mark.asyncio
async def test_get_all_exercises_returns_empty_list(exercise_api_client_factory):
    DummyExerciseApiService.list_response = []
    async for client, _ in exercise_api_client_factory():
        response = await client.get("/exercises/")
    assert response.status_code == 200
    assert response.json() == {"exercises": []}


@pytest.mark.asyncio
async def test_get_all_exercises_returns_500_when_service_fails(exercise_api_client_factory):
    DummyExerciseApiService.raise_on["get_all_exercises"] = RuntimeError("list failed")
    async for client, _ in exercise_api_client_factory():
        response = await client.get("/exercises/")
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_create_exercise_returns_201_and_created_exercise(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.post("/exercises/", json=build_exercise_payload())
    assert response.status_code == 201
    assert response.json()["id"] == str(EXERCISE_ID)
    assert DummyExerciseApiService.last_create_payload.title == "Free writing"


@pytest.mark.asyncio
async def test_create_exercise_validates_required_payload(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.post("/exercises/", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_exercise_returns_500_when_service_fails(exercise_api_client_factory):
    DummyExerciseApiService.raise_on["create_exercise"] = RuntimeError("create failed")
    async for client, _ in exercise_api_client_factory():
        response = await client.post("/exercises/", json=build_exercise_payload())
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_delete_exercise_returns_204(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.delete(f"/exercises/{EXERCISE_ID}")
    assert response.status_code == 204
    assert response.content == b""
    assert DummyExerciseApiService.last_exercise_id == EXERCISE_ID


@pytest.mark.asyncio
async def test_delete_exercise_validates_uuid(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.delete("/exercises/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_exercise_returns_404_when_missing(exercise_api_client_factory):
    DummyExerciseApiService.raise_on["delete_exercise"] = HTTPException(status_code=404)
    async for client, _ in exercise_api_client_factory():
        response = await client.delete(f"/exercises/{EXERCISE_ID}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_exercise_returns_detail(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.get(f"/exercises/{EXERCISE_ID}")
    assert response.status_code == 200
    assert response.json() == build_exercise_detail_response()
    assert DummyExerciseApiService.last_exercise_id == EXERCISE_ID
    assert DummyExerciseApiService.last_user_id == USER_ID


@pytest.mark.asyncio
async def test_get_exercise_validates_uuid(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.get("/exercises/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_exercise_returns_404_when_missing(exercise_api_client_factory):
    DummyExerciseApiService.raise_on["get_exercise_by_id"] = HTTPException(status_code=404)
    async for client, _ in exercise_api_client_factory():
        response = await client.get(f"/exercises/{EXERCISE_ID}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_field_returns_201(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.post(f"/exercises/{EXERCISE_ID}/fields/", json=build_field_payload())
    assert response.status_code == 201
    assert response.json()["id"] == str(FIELD_ID)
    assert DummyExerciseApiService.last_exercise_id == EXERCISE_ID
    assert DummyExerciseApiService.last_create_payload.title == "Mood reason"


@pytest.mark.asyncio
async def test_create_field_validates_payload_and_uuid(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        invalid_body_response = await client.post(f"/exercises/{EXERCISE_ID}/fields/", json={})
        invalid_uuid_response = await client.post("/exercises/not-a-uuid/fields/", json=build_field_payload())
    assert invalid_body_response.status_code == 422
    assert invalid_uuid_response.status_code == 422


@pytest.mark.asyncio
async def test_create_field_returns_404_when_exercise_missing(exercise_api_client_factory):
    DummyExerciseApiService.raise_on["create_field"] = HTTPException(status_code=404)
    async for client, _ in exercise_api_client_factory():
        response = await client.post(f"/exercises/{EXERCISE_ID}/fields/", json=build_field_payload())
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_field_returns_204(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.delete(f"/exercises/fields/{FIELD_ID}")
    assert response.status_code == 204
    assert DummyExerciseApiService.last_field_id == FIELD_ID


@pytest.mark.asyncio
async def test_delete_field_validates_uuid_and_missing_field(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        invalid_uuid_response = await client.delete("/exercises/fields/not-a-uuid")
    DummyExerciseApiService.raise_on["delete_field"] = HTTPException(status_code=404)
    async for client, _ in exercise_api_client_factory():
        missing_response = await client.delete(f"/exercises/fields/{FIELD_ID}")
    assert invalid_uuid_response.status_code == 422
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_create_variant_returns_201(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.post(f"/exercises/fields/{FIELD_ID}/variants/", json=build_variant_payload())
    assert response.status_code == 201
    assert response.json() == build_variant_response()
    assert DummyExerciseApiService.last_field_id == FIELD_ID


@pytest.mark.asyncio
async def test_create_variant_validates_payload_and_missing_field(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        invalid_body_response = await client.post(f"/exercises/fields/{FIELD_ID}/variants/", json={})
    DummyExerciseApiService.raise_on["create_variant"] = HTTPException(status_code=404)
    async for client, _ in exercise_api_client_factory():
        missing_response = await client.post(f"/exercises/fields/{FIELD_ID}/variants/", json=build_variant_payload())
    assert invalid_body_response.status_code == 422
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_variant_returns_204(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.delete(f"/exercises/variants/{VARIANT_ID}")
    assert response.status_code == 204
    assert DummyExerciseApiService.last_variant_id == VARIANT_ID


@pytest.mark.asyncio
async def test_delete_variant_validates_uuid_and_missing_variant(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        invalid_uuid_response = await client.delete("/exercises/variants/not-a-uuid")
    DummyExerciseApiService.raise_on["delete_variant"] = HTTPException(status_code=404)
    async for client, _ in exercise_api_client_factory():
        missing_response = await client.delete(f"/exercises/variants/{VARIANT_ID}")
    assert invalid_uuid_response.status_code == 422
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_create_exercise_view_returns_201(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.post(f"/exercises/{EXERCISE_ID}/views/", json=build_view_payload())
    assert response.status_code == 201
    assert response.json() == build_view_response()
    assert DummyExerciseApiService.last_exercise_id == EXERCISE_ID


@pytest.mark.asyncio
async def test_create_exercise_view_validates_payload_and_missing_exercise(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        invalid_body_response = await client.post(f"/exercises/{EXERCISE_ID}/views/", json={})
    DummyExerciseApiService.raise_on["create_exercise_view"] = HTTPException(status_code=404)
    async for client, _ in exercise_api_client_factory():
        missing_response = await client.post(f"/exercises/{EXERCISE_ID}/views/", json=build_view_payload())
    assert invalid_body_response.status_code == 422
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_exercise_view_returns_204(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.delete(f"/exercises/views/{VIEW_ID}")
    assert response.status_code == 204
    assert DummyExerciseApiService.last_view_id == VIEW_ID


@pytest.mark.asyncio
async def test_delete_exercise_view_validates_uuid_and_missing_view(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        invalid_uuid_response = await client.delete("/exercises/views/not-a-uuid")
    DummyExerciseApiService.raise_on["delete_exercise_view"] = HTTPException(status_code=404)
    async for client, _ in exercise_api_client_factory():
        missing_response = await client.delete(f"/exercises/views/{VIEW_ID}")
    assert invalid_uuid_response.status_code == 422
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_get_exercise_structure_returns_nested_payload(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.get(f"/exercises/{EXERCISE_ID}/structure")
    assert response.status_code == 200
    assert response.json()["pages"][0]["sections"][0]["variants"][0]["id"] == str(VARIANT_ID)


@pytest.mark.asyncio
async def test_get_exercise_structure_validates_uuid_and_missing_exercise(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        invalid_uuid_response = await client.get("/exercises/not-a-uuid/structure")
    DummyExerciseApiService.raise_on["get_exercise_structure_by_id"] = HTTPException(status_code=404)
    async for client, _ in exercise_api_client_factory():
        missing_response = await client.get(f"/exercises/{EXERCISE_ID}/structure")
    assert invalid_uuid_response.status_code == 422
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_get_exercise_results_returns_results(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.get(f"/exercises/{EXERCISE_ID}/results")
    assert response.status_code == 200
    assert response.json() == build_results_response()
    assert DummyExerciseApiService.last_user_id == USER_ID


@pytest.mark.asyncio
async def test_get_exercise_results_validates_uuid_and_handles_service_failure(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        invalid_uuid_response = await client.get("/exercises/not-a-uuid/results")
    DummyExerciseApiService.raise_on["get_exercise_results"] = RuntimeError("results failed")
    async for client, _ in exercise_api_client_factory():
        failure_response = await client.get(f"/exercises/{EXERCISE_ID}/results")
    assert invalid_uuid_response.status_code == 422
    assert failure_response.status_code == 500


@pytest.mark.asyncio
async def test_get_exercise_result_detail_returns_detail(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.get(f"/exercises/{EXERCISE_ID}/results/{RESULT_ID}")
    assert response.status_code == 200
    assert response.json() == build_result_detail_response()
    assert DummyExerciseApiService.last_exercise_id == EXERCISE_ID
    assert DummyExerciseApiService.last_create_payload == RESULT_ID


@pytest.mark.asyncio
async def test_get_exercise_result_detail_validates_ids_and_missing_result(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        invalid_uuid_response = await client.get(f"/exercises/{EXERCISE_ID}/results/not-a-uuid")
    DummyExerciseApiService.raise_on["get_exercise_result_detail"] = HTTPException(status_code=404)
    async for client, _ in exercise_api_client_factory():
        missing_response = await client.get(f"/exercises/{EXERCISE_ID}/results/{RESULT_ID}")
    assert invalid_uuid_response.status_code == 422
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_complete_exercise_returns_201(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        response = await client.post("/exercises/complete", json=build_complete_payload())
    assert response.status_code == 201
    assert response.json() == build_completed_response()
    user_id, completed_data = DummyExerciseApiService.last_complete_args
    assert user_id == USER_ID
    assert completed_data.exercise_structure_id == EXERCISE_ID


@pytest.mark.asyncio
async def test_complete_exercise_validates_payload_and_maps_value_error_to_400(exercise_api_client_factory):
    async for client, _ in exercise_api_client_factory():
        invalid_body_response = await client.post("/exercises/complete", json={})
    DummyExerciseApiService.raise_on["complete_exercise"] = HTTPException(status_code=400, detail="Exercise not found")
    async for client, _ in exercise_api_client_factory():
        bad_business_response = await client.post("/exercises/complete", json=build_complete_payload())
    assert invalid_body_response.status_code == 422
    assert bad_business_response.status_code == 400


@pytest.mark.asyncio
async def test_complete_exercise_returns_500_when_service_fails(exercise_api_client_factory):
    DummyExerciseApiService.raise_on["complete_exercise"] = RuntimeError("complete failed")
    async for client, _ in exercise_api_client_factory():
        response = await client.post("/exercises/complete", json=build_complete_payload())
    assert response.status_code == 500
