from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import select

import src.api.user_task as user_task_api_module
from autotest.factories.user_task import TASK_ID, USER_ID
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.models.user_task import UserTaskOrm


def build_task_orm(
    *,
    task_id=TASK_ID,
    text="Task from DB",
    created_at=datetime(2026, 4, 10, 10, 0, 0),
    completed_at=None,
    is_complete=False,
    user_id=USER_ID,
):
    return UserTaskOrm(
        id=task_id,
        text=text,
        created_at=created_at,
        completed_at=completed_at,
        is_complete=is_complete,
        user_id=user_id,
    )


@pytest.fixture
def user_task_integration_client_factory(api_client_factory, integration_db_manager_factory):
    def _factory(user_id=USER_ID):
        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                user_task_api_module.router,
                dependency_overrides={
                    get_db: integration_db_manager_factory,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client

        return _client()

    return _factory


async def fetch_task(session_factory, task_id):
    async with session_factory() as session:
        result = await session.execute(select(UserTaskOrm).filter_by(id=task_id))
        return result.scalars().one_or_none()


@pytest.mark.asyncio
async def test_user_task_create_and_actual_integration(
    user_task_integration_client_factory,
    integration_session_factory,
):
    async for client in user_task_integration_client_factory():
        create_response = await client.post("/user-task", json={"text": "Integration task"})
        actual_response = await client.get("/user-task/actual")

    assert create_response.status_code == 200
    assert create_response.json() == {"status": "OK"}
    assert actual_response.status_code == 200
    assert actual_response.json()[0]["text"] == "Integration task"

    async with integration_session_factory() as session:
        result = await session.execute(select(UserTaskOrm).filter_by(user_id=USER_ID))
        created = result.scalars().one()
        assert created.text == "Integration task"
        assert created.is_complete is False


@pytest.mark.asyncio
async def test_user_task_update_to_completed_and_get_completed_integration(
    user_task_integration_client_factory,
    integration_session_factory,
):
    async with integration_session_factory() as session:
        session.add(build_task_orm())
        await session.commit()

    async for client in user_task_integration_client_factory():
        update_response = await client.patch(
            "/user-task/update",
            json={"user_task_id": str(TASK_ID), "text": "Done task", "is_complete": True},
        )
        completed_response = await client.get(
            "/user-task/completed?start_date=2026-04-01T00:00:00&end_date=2026-04-30T23:59:59"
        )

    assert update_response.status_code == 200
    assert update_response.json() == {"status": "OK"}
    assert completed_response.status_code == 200
    assert completed_response.json()[0]["id"] == str(TASK_ID)
    assert completed_response.json()[0]["is_complete"] is True

    stored = await fetch_task(integration_session_factory, TASK_ID)
    assert stored.text == "Done task"
    assert stored.is_complete is True
    assert stored.completed_at is not None


@pytest.mark.asyncio
async def test_user_task_delete_integration_removes_row(
    user_task_integration_client_factory,
    integration_session_factory,
):
    async with integration_session_factory() as session:
        session.add(build_task_orm())
        await session.commit()

    async for client in user_task_integration_client_factory():
        response = await client.request("DELETE", "/user-task", json={"user_task_id": str(TASK_ID)})

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    assert await fetch_task(integration_session_factory, TASK_ID) is None

