import pytest

import src.api.diary as diary_api_module
from autotest.factories.diary import (
    DIARY_ID,
    USER_ID,
    build_add_diary_payload,
    build_diary_response,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.exceptions import (
    FutureDateError,
    InvalidDateFormatError,
    InvalidTimestampError,
    TextEmptyError,
    TextTooLongError,
)


class DummyDiaryApiService:
    diary_response = []
    by_month_response = []
    raise_on_get = None
    raise_on_add = None
    raise_on_by_month = None
    last_get_args = None
    last_add_args = None
    last_by_month_args = None

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.diary_response = []
        cls.by_month_response = []
        cls.raise_on_get = None
        cls.raise_on_add = None
        cls.raise_on_by_month = None
        cls.last_get_args = None
        cls.last_add_args = None
        cls.last_by_month_args = None

    async def get_diary(self, user_id, day):
        if type(self).raise_on_get:
            raise type(self).raise_on_get
        type(self).last_get_args = (user_id, day)
        return type(self).diary_response

    async def add_diary(self, data, user_id):
        if type(self).raise_on_add:
            raise type(self).raise_on_add
        type(self).last_add_args = (data, user_id)

    async def get_diary_for_month(self, timestamp, user_id):
        if type(self).raise_on_by_month:
            raise type(self).raise_on_by_month
        type(self).last_by_month_args = (timestamp, user_id)
        return type(self).by_month_response


@pytest.fixture
def diary_api_client_factory(api_client_factory, monkeypatch):
    DummyDiaryApiService.reset()
    monkeypatch.setattr(diary_api_module, "DiaryService", DummyDiaryApiService)

    def _factory(user_id=USER_ID):
        fake_db = object()

        async def override_get_db():
            yield fake_db

        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                diary_api_module.router,
                dependency_overrides={
                    get_db: override_get_db,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client, fake_db

        return _client()

    return _factory


@pytest.mark.asyncio
async def test_get_diary_returns_payload(diary_api_client_factory):
    DummyDiaryApiService.diary_response = [build_diary_response()]

    async for client, _ in diary_api_client_factory():
        response = await client.get("/diary")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(DIARY_ID)
    assert sorted(response.json()[0].keys()) == ["created_at", "id", "text", "user_id"]
    assert DummyDiaryApiService.last_get_args == (USER_ID, None)


@pytest.mark.asyncio
async def test_get_diary_accepts_day_query(diary_api_client_factory):
    async for client, _ in diary_api_client_factory():
        response = await client.get("/diary?day=2026-04-15")

    assert response.status_code == 200
    assert DummyDiaryApiService.last_get_args == (USER_ID, "2026-04-15")


@pytest.mark.asyncio
async def test_get_diary_returns_empty_list(diary_api_client_factory):
    async for client, _ in diary_api_client_factory():
        response = await client.get("/diary")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_diary_returns_400_for_invalid_day_format(diary_api_client_factory):
    DummyDiaryApiService.raise_on_get = InvalidDateFormatError()

    async for client, _ in diary_api_client_factory():
        response = await client.get("/diary?day=bad-date")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_diary_returns_500_for_unexpected_error(diary_api_client_factory):
    DummyDiaryApiService.raise_on_get = RuntimeError("boom")

    async for client, _ in diary_api_client_factory():
        response = await client.get("/diary")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_create_diary_returns_ok(diary_api_client_factory):
    async for client, _ in diary_api_client_factory():
        response = await client.post("/diary", json=build_add_diary_payload())

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    assert DummyDiaryApiService.last_add_args[1] == USER_ID
    assert DummyDiaryApiService.last_add_args[0].text == "Diary note"


@pytest.mark.asyncio
async def test_create_diary_returns_422_for_missing_text(diary_api_client_factory):
    payload = build_add_diary_payload()
    payload.pop("text")

    async for client, _ in diary_api_client_factory():
        response = await client.post("/diary", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_diary_returns_422_for_empty_body(diary_api_client_factory):
    async for client, _ in diary_api_client_factory():
        response = await client.post("/diary", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_diary_returns_422_for_empty_text(diary_api_client_factory):
    DummyDiaryApiService.raise_on_add = TextEmptyError()

    async for client, _ in diary_api_client_factory():
        response = await client.post("/diary", json=build_add_diary_payload(text="   "))

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_diary_returns_422_for_too_long_text(diary_api_client_factory):
    DummyDiaryApiService.raise_on_add = TextTooLongError()

    async for client, _ in diary_api_client_factory():
        response = await client.post("/diary", json=build_add_diary_payload(text="x" * 1001))

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_diary_returns_400_for_invalid_day_format(diary_api_client_factory):
    DummyDiaryApiService.raise_on_add = InvalidDateFormatError()

    async for client, _ in diary_api_client_factory():
        response = await client.post("/diary", json=build_add_diary_payload(day="bad-date"))

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_diary_returns_400_for_future_day(diary_api_client_factory):
    DummyDiaryApiService.raise_on_add = FutureDateError()

    async for client, _ in diary_api_client_factory():
        response = await client.post("/diary", json=build_add_diary_payload(day="2099-01-01"))

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_diary_returns_500_for_unexpected_error(diary_api_client_factory):
    DummyDiaryApiService.raise_on_add = RuntimeError("boom")

    async for client, _ in diary_api_client_factory():
        response = await client.post("/diary", json=build_add_diary_payload())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_diary_for_month_returns_payload(diary_api_client_factory):
    DummyDiaryApiService.by_month_response = [
        {"date": 1711929600, "diary": True},
        {"date": 1712016000, "diary": False},
    ]

    async for client, _ in diary_api_client_factory():
        response = await client.get("/diary/by_month?timestamp=1711929600")

    assert response.status_code == 200
    assert response.json()[0] == {"date": 1711929600, "diary": True}
    assert DummyDiaryApiService.last_by_month_args == (1711929600, USER_ID)


@pytest.mark.asyncio
async def test_get_diary_for_month_returns_empty_list(diary_api_client_factory):
    DummyDiaryApiService.by_month_response = []

    async for client, _ in diary_api_client_factory():
        response = await client.get("/diary/by_month?timestamp=1711929600")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_diary_for_month_returns_422_when_timestamp_missing(diary_api_client_factory):
    async for client, _ in diary_api_client_factory():
        response = await client.get("/diary/by_month")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_diary_for_month_returns_422_when_timestamp_is_not_positive(diary_api_client_factory):
    async for client, _ in diary_api_client_factory():
        response = await client.get("/diary/by_month?timestamp=0")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_diary_for_month_returns_422_for_invalid_timestamp_type(diary_api_client_factory):
    async for client, _ in diary_api_client_factory():
        response = await client.get("/diary/by_month?timestamp=bad")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_diary_for_month_returns_400_for_invalid_timestamp_error(diary_api_client_factory):
    DummyDiaryApiService.raise_on_by_month = InvalidTimestampError()

    async for client, _ in diary_api_client_factory():
        response = await client.get("/diary/by_month?timestamp=1711929600")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_diary_for_month_returns_500_for_unexpected_error(diary_api_client_factory):
    DummyDiaryApiService.raise_on_by_month = RuntimeError("boom")

    async for client, _ in diary_api_client_factory():
        response = await client.get("/diary/by_month?timestamp=1711929600")

    assert response.status_code == 500

