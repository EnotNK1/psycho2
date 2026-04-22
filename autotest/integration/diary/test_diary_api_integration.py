from datetime import datetime

import pytest
from sqlalchemy import select

import src.api.diary as diary_api_module
from autotest.factories.diary import DIARY_ID, USER_ID
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.models.diary import DiaryOrm


def build_diary_orm(
    *,
    diary_id=DIARY_ID,
    text="Diary from DB",
    created_at=datetime(2026, 4, 10, 10, 0, 0),
    user_id=USER_ID,
):
    return DiaryOrm(
        id=diary_id,
        text=text,
        created_at=created_at,
        user_id=user_id,
    )


@pytest.fixture
def diary_integration_client_factory(api_client_factory, integration_db_manager_factory):
    def _factory(user_id=USER_ID):
        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                diary_api_module.router,
                dependency_overrides={
                    get_db: integration_db_manager_factory,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client

        return _client()

    return _factory


async def fetch_diary(session_factory, diary_id):
    async with session_factory() as session:
        result = await session.execute(select(DiaryOrm).filter_by(id=diary_id))
        return result.scalars().one_or_none()


@pytest.mark.asyncio
async def test_diary_create_and_get_integration(
    diary_integration_client_factory,
    integration_session_factory,
):
    async for client in diary_integration_client_factory():
        create_response = await client.post("/diary", json={"text": "Integration diary", "day": "2024-04-10"})
        get_response = await client.get("/diary")

    assert create_response.status_code == 200
    assert create_response.json() == {"status": "OK"}
    assert get_response.status_code == 200
    assert get_response.json()[0]["text"] == "Integration diary"

    async with integration_session_factory() as session:
        result = await session.execute(select(DiaryOrm).filter_by(user_id=USER_ID))
        created = result.scalars().one()
        assert created.text == "Integration diary"


@pytest.mark.asyncio
async def test_diary_get_by_day_integration(
    diary_integration_client_factory,
    integration_session_factory,
):
    async with integration_session_factory() as session:
        session.add(build_diary_orm(created_at=datetime(2026, 4, 10, 9, 0, 0)))
        session.add(build_diary_orm(diary_id=__import__("uuid").uuid4(), created_at=datetime(2026, 4, 11, 9, 0, 0)))
        await session.commit()

    async for client in diary_integration_client_factory():
        response = await client.get("/diary?day=2026-04-10")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(DIARY_ID)


@pytest.mark.asyncio
async def test_diary_by_month_integration_returns_calendar(
    diary_integration_client_factory,
    integration_session_factory,
):
    async with integration_session_factory() as session:
        session.add(build_diary_orm(created_at=datetime(2026, 4, 2, 9, 0, 0)))
        session.add(build_diary_orm(diary_id=__import__("uuid").uuid4(), created_at=datetime(2026, 4, 20, 9, 0, 0)))
        await session.commit()

    async for client in diary_integration_client_factory():
        response = await client.get("/diary/by_month?timestamp=1775001600")

    assert response.status_code == 200
    assert len(response.json()) == 30
    assert response.json()[1]["diary"] is True
    assert response.json()[19]["diary"] is True

