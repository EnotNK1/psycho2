from datetime import date, timedelta

import pytest

import src.api.gamification as gamification_api_module
from autotest.factories.gamification import USER_ID, build_score_entry
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id


class DummyGamificationApiService:
    current_score_response = 10
    weekly_scores_response = [build_score_entry()]
    period_scores_response = [build_score_entry()]
    raise_on_current = None
    raise_on_weekly = None
    raise_on_period = None
    last_current_user_id = None
    last_weekly_user_id = None
    last_period_args = None

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.current_score_response = 10
        cls.weekly_scores_response = [build_score_entry()]
        cls.period_scores_response = [build_score_entry()]
        cls.raise_on_current = None
        cls.raise_on_weekly = None
        cls.raise_on_period = None
        cls.last_current_user_id = None
        cls.last_weekly_user_id = None
        cls.last_period_args = None

    async def get_current_score(self, user_id):
        if type(self).raise_on_current:
            raise type(self).raise_on_current
        type(self).last_current_user_id = user_id
        return type(self).current_score_response

    async def get_weekly_scores(self, user_id):
        if type(self).raise_on_weekly:
            raise type(self).raise_on_weekly
        type(self).last_weekly_user_id = user_id
        return type(self).weekly_scores_response

    async def get_scores_by_period(self, user_id, start_date, end_date):
        if type(self).raise_on_period:
            raise type(self).raise_on_period
        type(self).last_period_args = (user_id, start_date, end_date)
        return type(self).period_scores_response


@pytest.fixture
def gamification_api_client_factory(api_client_factory, monkeypatch):
    DummyGamificationApiService.reset()
    monkeypatch.setattr(gamification_api_module, "GamificationService", DummyGamificationApiService)

    def _factory(user_id=str(USER_ID)):
        fake_db = object()

        async def override_get_db():
            yield fake_db

        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                gamification_api_module.router,
                dependency_overrides={
                    get_db: override_get_db,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client, fake_db

        return _client()

    return _factory


@pytest.mark.asyncio
async def test_get_current_score_returns_wrapped_score(gamification_api_client_factory):
    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/current-score")

    assert response.status_code == 200
    assert response.json() == {"score": 10}
    assert DummyGamificationApiService.last_current_user_id == USER_ID


@pytest.mark.asyncio
async def test_get_current_score_returns_400_for_invalid_user_id(gamification_api_client_factory):
    async for client, _ in gamification_api_client_factory(user_id="bad-uuid"):
        response = await client.get("/gamification/current-score")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_current_score_returns_500_for_unexpected_error(gamification_api_client_factory):
    DummyGamificationApiService.raise_on_current = RuntimeError("boom")

    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/current-score")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_weekly_scores_returns_entries(gamification_api_client_factory):
    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/weekly-scores")

    assert response.status_code == 200
    assert response.json()["scores"][0]["score"] == 10
    assert DummyGamificationApiService.last_weekly_user_id == USER_ID


@pytest.mark.asyncio
async def test_get_weekly_scores_returns_empty_list(gamification_api_client_factory):
    DummyGamificationApiService.weekly_scores_response = []

    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/weekly-scores")

    assert response.status_code == 200
    assert response.json() == {"scores": []}


@pytest.mark.asyncio
async def test_get_weekly_scores_returns_400_for_invalid_user_id(gamification_api_client_factory):
    async for client, _ in gamification_api_client_factory(user_id="bad-uuid"):
        response = await client.get("/gamification/weekly-scores")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_weekly_scores_returns_500_for_unexpected_error(gamification_api_client_factory):
    DummyGamificationApiService.raise_on_weekly = RuntimeError("boom")

    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/weekly-scores")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_period_scores_returns_entries(gamification_api_client_factory):
    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/period-scores?start_date=2026-05-01&end_date=2026-05-06")

    assert response.status_code == 200
    assert response.json()["scores"][0]["score"] == 10
    user_id, start_date, end_date = DummyGamificationApiService.last_period_args
    assert user_id == USER_ID
    assert str(start_date) == "2026-05-01"
    assert str(end_date) == "2026-05-06"


@pytest.mark.asyncio
async def test_get_period_scores_returns_422_for_missing_query(gamification_api_client_factory):
    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/period-scores?start_date=2026-05-01")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_period_scores_returns_400_for_business_validation_error(gamification_api_client_factory):
    DummyGamificationApiService.raise_on_period = ValueError("Start date cannot be after end date")

    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/period-scores?start_date=2026-05-06&end_date=2026-05-01")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_period_scores_returns_400_for_invalid_user_id(gamification_api_client_factory):
    async for client, _ in gamification_api_client_factory(user_id="bad-uuid"):
        response = await client.get("/gamification/period-scores?start_date=2026-05-01&end_date=2026-05-06")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_period_scores_returns_500_for_unexpected_error(gamification_api_client_factory):
    DummyGamificationApiService.raise_on_period = RuntimeError("boom")

    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/period-scores?start_date=2026-05-01&end_date=2026-05-06")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_praise_returns_blank_payload_for_short_streak(gamification_api_client_factory):
    DummyGamificationApiService.period_scores_response = [build_score_entry(score=10)]

    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/praise")

    assert response.status_code == 200
    assert response.json() == {"consecutive_days": 0, "title": "", "subtitle": ""}


@pytest.mark.asyncio
async def test_get_praise_returns_title_for_3_day_streak(gamification_api_client_factory):
    today = date.today()
    DummyGamificationApiService.period_scores_response = [
        {"date": (today - timedelta(days=offset)).isoformat(), "score": 30}
        for offset in range(3)
    ]

    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/praise")

    assert response.status_code == 200
    assert response.json()["consecutive_days"] == 3
    assert response.json()["title"] == "Ты на верном пути"


@pytest.mark.asyncio
async def test_get_praise_returns_title_for_7_day_streak(gamification_api_client_factory):
    today = date.today()
    DummyGamificationApiService.period_scores_response = [
        {"date": (today - timedelta(days=offset)).isoformat(), "score": 30}
        for offset in range(7)
    ]

    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/praise")

    assert response.status_code == 200
    assert response.json()["consecutive_days"] == 7
    assert response.json()["title"] == "Неделя рядом с собой"


@pytest.mark.asyncio
async def test_get_praise_returns_title_for_14_day_streak(gamification_api_client_factory):
    today = date.today()
    DummyGamificationApiService.period_scores_response = [
        {"date": (today - timedelta(days=offset)).isoformat(), "score": 30}
        for offset in range(14)
    ]

    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/praise")

    assert response.status_code == 200
    assert response.json()["consecutive_days"] == 14
    assert response.json()["title"] == "Две недели заботы"


@pytest.mark.asyncio
async def test_get_praise_returns_title_for_30_day_streak(gamification_api_client_factory):
    today = date.today()
    DummyGamificationApiService.period_scores_response = [
        {"date": (today - timedelta(days=offset)).isoformat(), "score": 30}
        for offset in range(30)
    ]

    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/praise")

    assert response.status_code == 200
    assert response.json()["consecutive_days"] == 30
    assert response.json()["title"] == "Осознанный месяц"


@pytest.mark.asyncio
async def test_get_praise_ignores_invalid_date_items(gamification_api_client_factory):
    today = date.today()
    DummyGamificationApiService.period_scores_response = [
        {"date": object(), "score": 30},
        {"date": today.isoformat(), "score": 30},
    ]

    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/praise")

    assert response.status_code == 200
    assert response.json()["consecutive_days"] == 1


@pytest.mark.asyncio
async def test_get_praise_returns_500_for_unexpected_error(gamification_api_client_factory):
    DummyGamificationApiService.raise_on_period = RuntimeError("boom")

    async for client, _ in gamification_api_client_factory():
        response = await client.get("/gamification/praise")

    assert response.status_code == 500
