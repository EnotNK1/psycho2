from datetime import datetime

import pytest

import src.api.user_task as user_task_api_module
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from autotest4.factories.user_task import (
    TASK_ID,
    USER_ID,
    build_actual_task_payload,
    build_completed_task_payload,
)
from src.exceptions import (
    DateException,
    FutureDateError,
    InvalidDateFormatError,
    InvalidTimestampError,
    TextEmptyError,
    TextTooLongError,
)
class DummyUserTaskApiService:
    actual_response = []
    completed_response = []
    raise_on_actual = None
    raise_on_completed = None
    raise_on_add = None
    raise_on_update = None
    raise_on_delete = None
    last_init_db = None
    last_actual_args = None
    last_completed_args = None
    last_add_args = None
    last_update_args = None
    last_delete_args = None

    def __init__(self, db):
        self.db = db
        type(self).last_init_db = db

    @classmethod
    def reset(cls):
        cls.actual_response = []
        cls.completed_response = []
        cls.raise_on_actual = None
        cls.raise_on_completed = None
        cls.raise_on_add = None
        cls.raise_on_update = None
        cls.raise_on_delete = None
        cls.last_init_db = None
        cls.last_actual_args = None
        cls.last_completed_args = None
        cls.last_add_args = None
        cls.last_update_args = None
        cls.last_delete_args = None

    async def get_actual_user_tasks(self, user_id, day):
        if type(self).raise_on_actual:
            raise type(self).raise_on_actual
        type(self).last_actual_args = (user_id, day)
        return type(self).actual_response

    async def get_completed_user_tasks(self, user_id, start_date, end_date):
        if type(self).raise_on_completed:
            raise type(self).raise_on_completed
        type(self).last_completed_args = (user_id, start_date, end_date)
        return type(self).completed_response

    async def add_user_task(self, data, user_id):
        if type(self).raise_on_add:
            raise type(self).raise_on_add
        type(self).last_add_args = (data, user_id)

    async def update_user_task(self, data):
        if type(self).raise_on_update:
            raise type(self).raise_on_update
        type(self).last_update_args = data

    async def delete(self, data):
        if type(self).raise_on_delete:
            raise type(self).raise_on_delete
        type(self).last_delete_args = data
        return {"status": "OK"}


@pytest.fixture
def user_task_api_client_factory(api_client_factory, monkeypatch):
    DummyUserTaskApiService.reset()
    monkeypatch.setattr(user_task_api_module, "UserTaskService", DummyUserTaskApiService)

    def _factory(user_id=USER_ID):
        fake_db = object()

        async def override_get_db():
            yield fake_db

        def override_get_current_user_id():
            return user_id

        dependency_overrides = {
            get_db: override_get_db,
            get_current_user_id: override_get_current_user_id,
        }

        async def _client():
            async for async_client, _ in api_client_factory(
                user_task_api_module.router,
                dependency_overrides=dependency_overrides,
            ):
                yield async_client, fake_db

        return _client()

    return _factory


@pytest.mark.asyncio
async def test_get_actual_user_task_returns_service_payload(user_task_api_client_factory):
    DummyUserTaskApiService.actual_response = [build_actual_task_payload()]

    async for client, fake_db in user_task_api_client_factory():
        response = await client.get("/user-task/actual")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(TASK_ID)
    assert sorted(response.json()[0].keys()) == ["created_at", "id", "is_complete", "text", "user_id"]
    assert DummyUserTaskApiService.last_init_db is fake_db
    assert DummyUserTaskApiService.last_actual_args == (USER_ID, None)


@pytest.mark.asyncio
async def test_get_actual_user_task_accepts_day_query(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.get("/user-task/actual?day=2026-04-10T12:00:00")

    assert response.status_code == 200
    assert DummyUserTaskApiService.last_actual_args[0] == USER_ID
    assert DummyUserTaskApiService.last_actual_args[1] == datetime(2026, 4, 10, 12, 0, 0)


@pytest.mark.asyncio
async def test_get_actual_user_task_returns_empty_list_when_service_returns_empty(user_task_api_client_factory):
    DummyUserTaskApiService.actual_response = []

    async for client, _ in user_task_api_client_factory():
        response = await client.get("/user-task/actual")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_actual_user_task_returns_422_for_invalid_day_format(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.get("/user-task/actual?day=not-a-date")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_actual_user_task_maps_invalid_date_format_error(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_actual = InvalidDateFormatError()

    async for client, _ in user_task_api_client_factory():
        response = await client.get("/user-task/actual")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_actual_user_task_maps_unexpected_error_to_500(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_actual = RuntimeError("boom")

    async for client, _ in user_task_api_client_factory():
        response = await client.get("/user-task/actual")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_completed_user_task_returns_service_payload(user_task_api_client_factory):
    DummyUserTaskApiService.completed_response = [build_completed_task_payload()]

    async for client, _ in user_task_api_client_factory():
        response = await client.get("/user-task/completed")

    assert response.status_code == 200
    assert response.json()[0]["is_complete"] is True
    assert sorted(response.json()[0].keys()) == [
        "completed_at",
        "created_at",
        "id",
        "is_complete",
        "text",
        "user_id",
    ]
    assert DummyUserTaskApiService.last_completed_args == (USER_ID, None, None)


@pytest.mark.asyncio
async def test_get_completed_user_task_accepts_date_range(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.get(
            "/user-task/completed?start_date=2026-04-01T00:00:00&end_date=2026-04-10T23:59:59"
        )

    assert response.status_code == 200
    assert DummyUserTaskApiService.last_completed_args == (
        USER_ID,
        datetime(2026, 4, 1, 0, 0, 0),
        datetime(2026, 4, 10, 23, 59, 59),
    )


@pytest.mark.asyncio
async def test_get_completed_user_task_returns_empty_list_when_service_returns_empty(user_task_api_client_factory):
    DummyUserTaskApiService.completed_response = []

    async for client, _ in user_task_api_client_factory():
        response = await client.get("/user-task/completed")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_completed_user_task_returns_422_for_invalid_start_date(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.get("/user-task/completed?start_date=bad&end_date=2026-04-10T00:00:00")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_completed_user_task_returns_422_for_invalid_end_date(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.get("/user-task/completed?start_date=2026-04-01T00:00:00&end_date=bad")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_completed_user_task_maps_date_exception(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_completed = DateException()

    async for client, _ in user_task_api_client_factory():
        response = await client.get("/user-task/completed")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_completed_user_task_maps_invalid_date_format_error(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_completed = InvalidDateFormatError()

    async for client, _ in user_task_api_client_factory():
        response = await client.get("/user-task/completed")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_completed_user_task_maps_unexpected_error_to_500(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_completed = RuntimeError("boom")

    async for client, _ in user_task_api_client_factory():
        response = await client.get("/user-task/completed")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_create_user_task_returns_ok(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.post("/user-task", json={"text": "New task"})

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    assert DummyUserTaskApiService.last_add_args[0].text == "New task"
    assert DummyUserTaskApiService.last_add_args[1] == USER_ID


@pytest.mark.asyncio
async def test_create_user_task_returns_422_when_body_missing_entirely(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.post("/user-task")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_task_returns_422_when_text_missing(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.post("/user-task", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_task_maps_text_empty_error(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_add = TextEmptyError()

    async for client, _ in user_task_api_client_factory():
        response = await client.post("/user-task", json={"text": ""})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_task_maps_text_too_long_error(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_add = TextTooLongError()

    async for client, _ in user_task_api_client_factory():
        response = await client.post("/user-task", json={"text": "x" * 5000})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_task_maps_invalid_date_format_error(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_add = InvalidDateFormatError()

    async for client, _ in user_task_api_client_factory():
        response = await client.post("/user-task", json={"text": "Task"})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_user_task_maps_future_date_error(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_add = FutureDateError()

    async for client, _ in user_task_api_client_factory():
        response = await client.post("/user-task", json={"text": "Task"})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_user_task_maps_unexpected_error_to_500(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_add = RuntimeError("boom")

    async for client, _ in user_task_api_client_factory():
        response = await client.post("/user-task", json={"text": "Task"})

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_update_user_task_returns_ok_for_text_only(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.patch(
            "/user-task/update",
            json={"user_task_id": str(TASK_ID), "text": "Updated"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    assert DummyUserTaskApiService.last_update_args.user_task_id == TASK_ID
    assert DummyUserTaskApiService.last_update_args.text == "Updated"
    assert DummyUserTaskApiService.last_update_args.is_complete is None


@pytest.mark.asyncio
async def test_update_user_task_returns_ok_for_completion_only(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.patch(
            "/user-task/update",
            json={"user_task_id": str(TASK_ID), "is_complete": True},
        )

    assert response.status_code == 200
    assert DummyUserTaskApiService.last_update_args.is_complete is True


@pytest.mark.asyncio
async def test_update_user_task_returns_ok_for_text_and_completion(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.patch(
            "/user-task/update",
            json={"user_task_id": str(TASK_ID), "text": "Done", "is_complete": False},
        )

    assert response.status_code == 200
    assert DummyUserTaskApiService.last_update_args.text == "Done"
    assert DummyUserTaskApiService.last_update_args.is_complete is False


@pytest.mark.asyncio
async def test_update_user_task_accepts_empty_optional_fields_and_returns_ok(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.patch(
            "/user-task/update",
            json={"user_task_id": str(TASK_ID)},
        )

    assert response.status_code == 200
    assert DummyUserTaskApiService.last_update_args.text is None
    assert DummyUserTaskApiService.last_update_args.is_complete is None


@pytest.mark.asyncio
async def test_update_user_task_returns_422_when_uuid_invalid(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.patch(
            "/user-task/update",
            json={"user_task_id": "bad-uuid", "text": "Updated"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_task_returns_422_when_is_complete_has_invalid_type(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.patch(
            "/user-task/update",
            json={"user_task_id": str(TASK_ID), "is_complete": "not-bool"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_task_returns_422_when_user_task_id_missing(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.patch("/user-task/update", json={"text": "Updated"})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_task_maps_text_empty_error(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_update = TextEmptyError()

    async for client, _ in user_task_api_client_factory():
        response = await client.patch(
            "/user-task/update",
            json={"user_task_id": str(TASK_ID), "text": ""},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_task_maps_text_too_long_error(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_update = TextTooLongError()

    async for client, _ in user_task_api_client_factory():
        response = await client.patch(
            "/user-task/update",
            json={"user_task_id": str(TASK_ID), "text": "x" * 5000},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_task_maps_invalid_date_format_error(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_update = InvalidDateFormatError()

    async for client, _ in user_task_api_client_factory():
        response = await client.patch(
            "/user-task/update",
            json={"user_task_id": str(TASK_ID), "text": "Task"},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_user_task_maps_future_date_error(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_update = FutureDateError()

    async for client, _ in user_task_api_client_factory():
        response = await client.patch(
            "/user-task/update",
            json={"user_task_id": str(TASK_ID), "text": "Task"},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_user_task_maps_unexpected_error_to_500(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_update = RuntimeError("boom")

    async for client, _ in user_task_api_client_factory():
        response = await client.patch(
            "/user-task/update",
            json={"user_task_id": str(TASK_ID), "text": "Task"},
        )

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_delete_user_task_returns_ok(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.request(
            "DELETE",
            "/user-task",
            json={"user_task_id": str(TASK_ID)},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    assert DummyUserTaskApiService.last_delete_args.user_task_id == TASK_ID


@pytest.mark.asyncio
async def test_delete_user_task_returns_422_when_body_missing_entirely(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.request("DELETE", "/user-task")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_user_task_returns_422_for_invalid_uuid(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.request(
            "DELETE",
            "/user-task",
            json={"user_task_id": "bad-uuid"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_user_task_returns_422_when_body_missing(user_task_api_client_factory):
    async for client, _ in user_task_api_client_factory():
        response = await client.request("DELETE", "/user-task", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_user_task_maps_invalid_timestamp_error(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_delete = InvalidTimestampError()

    async for client, _ in user_task_api_client_factory():
        response = await client.request(
            "DELETE",
            "/user-task",
            json={"user_task_id": str(TASK_ID)},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_user_task_maps_unexpected_error_to_500(user_task_api_client_factory):
    DummyUserTaskApiService.raise_on_delete = RuntimeError("boom")

    async for client, _ in user_task_api_client_factory():
        response = await client.request(
            "DELETE",
            "/user-task",
            json={"user_task_id": str(TASK_ID)},
        )

    assert response.status_code == 500
