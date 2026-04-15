import pytest

import src.api.mood_tracker as mood_tracker_api_module
from autotest4.factories.mood_tracker import (
    MOOD_TRACKER_ID,
    USER_ID,
    build_add_mood_payload,
    build_mood_tracker_response,
    make_emoji,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id


class DummyMoodTrackerSmokeService:
    def __init__(self, db):
        self.db = db

    async def save_mood_tracker(self, data, user_id):
        return None

    async def get_mood_tracker(self, day, user_id):
        return [build_mood_tracker_response()]

    async def get_weekly_mood_tracker(self, user_id):
        return [build_mood_tracker_response()]

    async def get_mood_tracker_by_period(self, user_id, start_date, end_date):
        return [build_mood_tracker_response()]

    async def get_mood_tracker_by_id(self, mood_tracker_id, user_id):
        return build_mood_tracker_response(mood_tracker_id=mood_tracker_id)


class DummyEmojiSmokeService:
    def __init__(self, db):
        self.db = db

    async def get_all_emojis(self):
        return [make_emoji(emoji_id=1, text="happy")]

    async def get_emoji_by_id(self, emoji_id):
        return make_emoji(emoji_id=emoji_id, text="happy")


@pytest.fixture
async def client(api_client_factory, monkeypatch):
    monkeypatch.setattr(mood_tracker_api_module, "MoodTrackerService", DummyMoodTrackerSmokeService)
    monkeypatch.setattr(mood_tracker_api_module, "EmojiService", DummyEmojiSmokeService)

    async def override_get_db():
        yield object()

    def override_get_current_user_id():
        return USER_ID

    async for async_client, _ in api_client_factory(
        mood_tracker_api_module.router,
        dependency_overrides={
            get_db: override_get_db,
            get_current_user_id: override_get_current_user_id,
        },
    ):
        yield async_client


@pytest.mark.asyncio
async def test_mood_tracker_add_smoke(client):
    response = await client.post("/mood_tracker", json=build_add_mood_payload())

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


@pytest.mark.asyncio
async def test_mood_tracker_get_smoke(client):
    response = await client.get("/mood_tracker")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(MOOD_TRACKER_ID)


@pytest.mark.asyncio
async def test_mood_tracker_emoji_smoke(client):
    response = await client.get("/mood_tracker/emoji")

    assert response.status_code == 200
    assert response.json()[0]["id"] == 1


@pytest.mark.asyncio
async def test_mood_tracker_period_smoke(client):
    response = await client.get("/mood_tracker/period?start_date=2026-04-01&end_date=2026-04-15")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(MOOD_TRACKER_ID)


@pytest.mark.asyncio
async def test_mood_tracker_by_id_smoke(client):
    response = await client.get(f"/mood_tracker/{MOOD_TRACKER_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(MOOD_TRACKER_ID)
