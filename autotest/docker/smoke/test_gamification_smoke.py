from datetime import date, timedelta

import pytest

import src.api.gamification as gamification_api_module
from autotest.factories.gamification import USER_ID, build_score_entry
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id


class DummyGamificationSmokeService:
    def __init__(self, db):
        self.db = db

    async def get_current_score(self, user_id):
        return 25

    async def get_weekly_scores(self, user_id):
        return [
            build_score_entry(score_date=date.today(), score=25),
            build_score_entry(score_date=date.today() - timedelta(days=1), score=30),
        ]

    async def get_scores_by_period(self, user_id, start_date, end_date):
        return [
            build_score_entry(score_date=end_date - timedelta(days=1), score=30),
            build_score_entry(score_date=end_date, score=35),
        ]


@pytest.fixture
async def client(api_client_factory, monkeypatch):
    monkeypatch.setattr(gamification_api_module, "GamificationService", DummyGamificationSmokeService)

    async def override_get_db():
        yield object()

    def override_get_current_user_id():
        return str(USER_ID)

    async for async_client, _ in api_client_factory(
        gamification_api_module.router,
        dependency_overrides={
            get_db: override_get_db,
            get_current_user_id: override_get_current_user_id,
        },
    ):
        yield async_client


@pytest.mark.asyncio
async def test_gamification_current_score_smoke(client):
    response = await client.get("/gamification/current-score")

    assert response.status_code == 200
    assert response.json() == {"score": 25}


@pytest.mark.asyncio
async def test_gamification_weekly_scores_smoke(client):
    response = await client.get("/gamification/weekly-scores")

    assert response.status_code == 200
    assert len(response.json()["scores"]) == 2
    assert response.json()["scores"][0]["score"] == 25


@pytest.mark.asyncio
async def test_gamification_period_scores_smoke(client):
    response = await client.get("/gamification/period-scores?start_date=2026-04-01&end_date=2026-04-07")

    assert response.status_code == 200
    assert len(response.json()["scores"]) == 2
    assert response.json()["scores"][1]["score"] == 35


@pytest.mark.asyncio
async def test_gamification_praise_smoke(client):
    response = await client.get("/gamification/praise")

    assert response.status_code == 200
    assert response.json()["consecutive_days"] == 2
    assert "title" in response.json()
    assert "subtitle" in response.json()
