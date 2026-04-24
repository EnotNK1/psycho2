import pytest

import src.api.diary as diary_api_module
from autotest.factories.diary import DIARY_ID, USER_ID, build_add_diary_payload, build_diary_response
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id


class DummyDiarySmokeService:
    def __init__(self, db):
        self.db = db

    async def get_diary(self, user_id, day):
        return [build_diary_response()]

    async def add_diary(self, data, user_id):
        return None

    async def get_diary_for_month(self, timestamp, user_id):
        return [{"date": 1711929600, "diary": True}]


@pytest.fixture
async def client(api_client_factory, monkeypatch):
    monkeypatch.setattr(diary_api_module, "DiaryService", DummyDiarySmokeService)

    async def override_get_db():
        yield object()

    def override_get_current_user_id():
        return USER_ID

    async for async_client, _ in api_client_factory(
        diary_api_module.router,
        dependency_overrides={
            get_db: override_get_db,
            get_current_user_id: override_get_current_user_id,
        },
    ):
        yield async_client


@pytest.mark.asyncio
async def test_diary_get_smoke(client):
    response = await client.get("/diary")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(DIARY_ID)


@pytest.mark.asyncio
async def test_diary_create_smoke(client):
    response = await client.post("/diary", json=build_add_diary_payload())

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


@pytest.mark.asyncio
async def test_diary_by_month_smoke(client):
    response = await client.get("/diary/by_month?timestamp=1711929600")

    assert response.status_code == 200
    assert response.json()[0] == {"date": 1711929600, "diary": True}
