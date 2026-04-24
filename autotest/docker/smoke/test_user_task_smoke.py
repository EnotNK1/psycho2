import pytest

import src.api.user_task as user_task_api_module
from autotest.factories.user_task import TASK_ID, USER_ID, build_actual_task_payload
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id


class DummyUserTaskSmokeService:
    def __init__(self, db):
        self.db = db

    async def get_actual_user_tasks(self, user_id, day):
        return [build_actual_task_payload(user_id=user_id)]

    async def get_completed_user_tasks(self, user_id, start_date, end_date):
        return []

    async def add_user_task(self, data, user_id):
        return None

    async def update_user_task(self, data):
        return None

    async def delete(self, data):
        return {"status": "OK"}


@pytest.fixture
async def client(api_client_factory, monkeypatch):
    monkeypatch.setattr(user_task_api_module, "UserTaskService", DummyUserTaskSmokeService)

    async def override_get_db():
        yield object()

    def override_get_current_user_id():
        return USER_ID

    async for async_client, _ in api_client_factory(
        user_task_api_module.router,
        dependency_overrides={
            get_db: override_get_db,
            get_current_user_id: override_get_current_user_id,
        },
    ):
        yield async_client


@pytest.mark.asyncio
async def test_user_task_actual_smoke(client):
    response = await client.get("/user-task/actual")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(TASK_ID)


@pytest.mark.asyncio
async def test_user_task_create_smoke(client):
    response = await client.post("/user-task", json={"text": "New task"})

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


@pytest.mark.asyncio
async def test_user_task_update_smoke(client):
    response = await client.patch(
        "/user-task/update",
        json={"user_task_id": str(TASK_ID), "text": "Updated"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
