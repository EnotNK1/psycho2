from datetime import datetime

import pytest
from sqlalchemy import select

from autotest.factories.user_task import TASK_ID, USER_ID
from src.models.user_task import UserTaskOrm
from src.services.user_task import UserTaskService


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


@pytest.mark.asyncio
async def test_user_task_service_add_and_get_actual_integration(integration_db, integration_session_factory):
    await UserTaskService(integration_db).add_user_task(type("Req", (), {"text": "Service task"})(), USER_ID)

    actual_tasks = await UserTaskService(integration_db).get_actual_user_tasks(USER_ID, None)

    assert actual_tasks[0]["text"] == "Service task"

    async with integration_session_factory() as session:
        result = await session.execute(select(UserTaskOrm).filter_by(user_id=USER_ID))
        stored = result.scalars().one()
        assert stored.text == "Service task"


@pytest.mark.asyncio
async def test_user_task_service_update_complete_and_get_completed_integration(
    integration_db,
    integration_session_factory,
):
    async with integration_session_factory() as session:
        session.add(build_task_orm())
        await session.commit()

    await UserTaskService(integration_db).update_user_task(
        type("Req", (), {"user_task_id": TASK_ID, "text": "Updated", "is_complete": True})()
    )

    completed = await UserTaskService(integration_db).get_completed_user_tasks(
        USER_ID,
        datetime(2026, 4, 1, 0, 0, 0),
        datetime(2026, 4, 30, 23, 59, 59),
    )

    assert completed[0]["id"] == str(TASK_ID)
    assert completed[0]["is_complete"] is True


@pytest.mark.asyncio
async def test_user_task_service_delete_integration(integration_db, integration_session_factory):
    async with integration_session_factory() as session:
        session.add(build_task_orm())
        await session.commit()

    await UserTaskService(integration_db).delete(type("Req", (), {"user_task_id": TASK_ID})())

    async with integration_session_factory() as session:
        result = await session.execute(select(UserTaskOrm).filter_by(id=TASK_ID))
        assert result.scalars().one_or_none() is None
