import pytest

import src.api.mood_tracker as mood_tracker_api_module
from autotest.factories.mood_tracker import (
    MOOD_TRACKER_ID,
    SECOND_MOOD_TRACKER_ID,
    SECOND_USER_ID,
    USER_ID,
    build_add_mood_payload,
    build_mood_tracker_response,
    make_emoji,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.exceptions import InvalidEmojiIdException, NotOwnedError, ScoreOutOfRangeError


class DummyMoodTrackerApiService:
    mood_tracker_response = []
    weekly_response = []
    period_response = []
    by_id_response = None
    raise_on_add = None
    raise_on_get = None
    raise_on_weekly = None
    raise_on_period = None
    raise_on_by_id = None
    last_add_args = None
    last_get_args = None
    last_weekly_user_id = None
    last_period_args = None
    last_by_id_args = None

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.mood_tracker_response = []
        cls.weekly_response = []
        cls.period_response = []
        cls.by_id_response = None
        cls.raise_on_add = None
        cls.raise_on_get = None
        cls.raise_on_weekly = None
        cls.raise_on_period = None
        cls.raise_on_by_id = None
        cls.last_add_args = None
        cls.last_get_args = None
        cls.last_weekly_user_id = None
        cls.last_period_args = None
        cls.last_by_id_args = None

    async def save_mood_tracker(self, data, user_id):
        if type(self).raise_on_add:
            raise type(self).raise_on_add
        type(self).last_add_args = (data, user_id)

    async def get_mood_tracker(self, day, user_id):
        if type(self).raise_on_get:
            raise type(self).raise_on_get
        type(self).last_get_args = (day, user_id)
        return type(self).mood_tracker_response

    async def get_weekly_mood_tracker(self, user_id):
        if type(self).raise_on_weekly:
            raise type(self).raise_on_weekly
        type(self).last_weekly_user_id = user_id
        return type(self).weekly_response

    async def get_mood_tracker_by_period(self, user_id, start_date, end_date):
        if type(self).raise_on_period:
            raise type(self).raise_on_period
        type(self).last_period_args = (user_id, start_date, end_date)
        return type(self).period_response

    async def get_mood_tracker_by_id(self, mood_tracker_id, user_id):
        if type(self).raise_on_by_id:
            raise type(self).raise_on_by_id
        type(self).last_by_id_args = (mood_tracker_id, user_id)
        return type(self).by_id_response


class DummyEmojiApiService:
    all_emojis_response = []
    by_id_response = None
    raise_on_get_all = None
    raise_on_get_by_id = None
    last_emoji_id = None

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.all_emojis_response = []
        cls.by_id_response = None
        cls.raise_on_get_all = None
        cls.raise_on_get_by_id = None
        cls.last_emoji_id = None

    async def get_all_emojis(self):
        if type(self).raise_on_get_all:
            raise type(self).raise_on_get_all
        return type(self).all_emojis_response

    async def get_emoji_by_id(self, emoji_id):
        if type(self).raise_on_get_by_id:
            raise type(self).raise_on_get_by_id
        type(self).last_emoji_id = emoji_id
        return type(self).by_id_response


@pytest.fixture
def mood_tracker_api_client_factory(api_client_factory, monkeypatch):
    DummyMoodTrackerApiService.reset()
    DummyEmojiApiService.reset()
    monkeypatch.setattr(mood_tracker_api_module, "MoodTrackerService", DummyMoodTrackerApiService)
    monkeypatch.setattr(mood_tracker_api_module, "EmojiService", DummyEmojiApiService)

    def _factory(user_id=USER_ID):
        fake_db = object()

        async def override_get_db():
            yield fake_db

        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                mood_tracker_api_module.router,
                dependency_overrides={
                    get_db: override_get_db,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client, fake_db

        return _client()

    return _factory


@pytest.mark.asyncio
async def test_add_mood_tracker_returns_ok(mood_tracker_api_client_factory):
    async for client, _ in mood_tracker_api_client_factory():
        response = await client.post("/mood_tracker", json=build_add_mood_payload())

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    assert DummyMoodTrackerApiService.last_add_args[1] == USER_ID
    assert DummyMoodTrackerApiService.last_add_args[0].score == 55


@pytest.mark.asyncio
async def test_add_mood_tracker_returns_422_for_score_out_of_range(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.raise_on_add = ScoreOutOfRangeError()

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.post("/mood_tracker", json=build_add_mood_payload())

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_mood_tracker_returns_400_for_invalid_emoji_ids(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.raise_on_add = InvalidEmojiIdException()

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.post("/mood_tracker", json=build_add_mood_payload())

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_add_mood_tracker_returns_422_for_invalid_day_format(mood_tracker_api_client_factory):
    async for client, _ in mood_tracker_api_client_factory():
        response = await client.post("/mood_tracker", json=build_add_mood_payload(day="not-a-date"))

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_mood_tracker_returns_422_for_missing_required_fields(mood_tracker_api_client_factory):
    payload = build_add_mood_payload()
    payload.pop("score")

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.post("/mood_tracker", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_mood_tracker_returns_500_for_unexpected_error(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.raise_on_add = RuntimeError("boom")

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.post("/mood_tracker", json=build_add_mood_payload())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_mood_tracker_returns_payload(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.mood_tracker_response = [build_mood_tracker_response()]

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(MOOD_TRACKER_ID)
    assert sorted(response.json()[0].keys()) == [
        "created_at",
        "emoji_ids",
        "emoji_texts",
        "id",
        "score",
        "user_id",
    ]
    assert DummyMoodTrackerApiService.last_get_args == (None, USER_ID)


@pytest.mark.asyncio
async def test_get_mood_tracker_accepts_day_query(mood_tracker_api_client_factory):
    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker?day=2026-04-15")

    assert response.status_code == 200
    assert DummyMoodTrackerApiService.last_get_args == ("2026-04-15", USER_ID)


@pytest.mark.asyncio
async def test_get_mood_tracker_returns_empty_list(mood_tracker_api_client_factory):
    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_mood_tracker_should_return_400_for_invalid_day_format(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.raise_on_get = ValueError("bad day")

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker?day=bad-date")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_mood_tracker_returns_500_for_unexpected_error(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.raise_on_get = RuntimeError("boom")

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_emoji_returns_all_emojis_when_id_missing(mood_tracker_api_client_factory):
    DummyEmojiApiService.all_emojis_response = [make_emoji(emoji_id=1, text="happy"), make_emoji(emoji_id=2, text="calm")]

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/emoji")

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_emoji_returns_single_emoji_by_id(mood_tracker_api_client_factory):
    DummyEmojiApiService.by_id_response = make_emoji(emoji_id=2, text="calm")

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/emoji?emoji_id=2")

    assert response.status_code == 200
    assert response.json()["id"] == 2
    assert DummyEmojiApiService.last_emoji_id == 2


@pytest.mark.asyncio
async def test_get_emoji_should_return_404_when_emoji_not_found(mood_tracker_api_client_factory):
    DummyEmojiApiService.by_id_response = None

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/emoji?emoji_id=2")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_emoji_returns_422_for_invalid_emoji_id_type(mood_tracker_api_client_factory):
    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/emoji?emoji_id=bad")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_emoji_returns_500_for_unexpected_error(mood_tracker_api_client_factory):
    DummyEmojiApiService.raise_on_get_all = RuntimeError("boom")

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/emoji")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_weekly_mood_tracker_returns_payload(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.weekly_response = [build_mood_tracker_response()]

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/weekly")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(MOOD_TRACKER_ID)
    assert DummyMoodTrackerApiService.last_weekly_user_id == USER_ID


@pytest.mark.asyncio
async def test_get_weekly_mood_tracker_returns_empty_list(mood_tracker_api_client_factory):
    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/weekly")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_weekly_mood_tracker_returns_500_for_unexpected_error(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.raise_on_weekly = RuntimeError("boom")

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/weekly")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_mood_tracker_by_period_returns_payload(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.period_response = [build_mood_tracker_response(mood_tracker_id=SECOND_MOOD_TRACKER_ID)]

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/period?start_date=2026-04-01&end_date=2026-04-15")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(SECOND_MOOD_TRACKER_ID)
    assert DummyMoodTrackerApiService.last_period_args == (USER_ID, "2026-04-01", "2026-04-15")


@pytest.mark.asyncio
async def test_get_mood_tracker_by_period_returns_422_when_required_query_missing(mood_tracker_api_client_factory):
    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/period?start_date=2026-04-01")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_mood_tracker_by_period_should_return_400_for_invalid_date_format(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.raise_on_period = ValueError("bad period")

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/period?start_date=bad&end_date=2026-04-15")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_mood_tracker_by_period_returns_500_for_unexpected_error(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.raise_on_period = RuntimeError("boom")

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/period?start_date=2026-04-01&end_date=2026-04-15")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_mood_tracker_by_id_returns_payload(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.by_id_response = build_mood_tracker_response()

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get(f"/mood_tracker/{MOOD_TRACKER_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(MOOD_TRACKER_ID)
    assert DummyMoodTrackerApiService.last_by_id_args == (MOOD_TRACKER_ID, USER_ID)


@pytest.mark.asyncio
async def test_get_mood_tracker_by_id_returns_403_when_record_not_owned(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.raise_on_by_id = NotOwnedError()

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get(f"/mood_tracker/{MOOD_TRACKER_ID}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_mood_tracker_by_id_returns_422_for_invalid_uuid(mood_tracker_api_client_factory):
    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get("/mood_tracker/not-a-uuid")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_mood_tracker_by_id_should_return_404_when_record_missing(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.raise_on_by_id = AttributeError("record missing")

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get(f"/mood_tracker/{MOOD_TRACKER_ID}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_mood_tracker_by_id_returns_500_for_unexpected_error(mood_tracker_api_client_factory):
    DummyMoodTrackerApiService.raise_on_by_id = RuntimeError("boom")

    async for client, _ in mood_tracker_api_client_factory():
        response = await client.get(f"/mood_tracker/{MOOD_TRACKER_ID}")

    assert response.status_code == 500
