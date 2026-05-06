from datetime import date, timedelta

import pytest

from autotest.factories.gamification import SECOND_USER_ID, USER_ID
from src.models.gamification import UserScoreOrm


@pytest.mark.asyncio
async def test_gamification_current_score_weekly_and_period_endpoints_integration(
    gamification_integration_client_factory,
    gamification_session_factory,
):
    from autotest.integration.gamification.conftest import build_user_orm

    today = date.today()
    async with gamification_session_factory() as session:
        session.add(build_user_orm(USER_ID))
        await session.commit()
        session.add(
            UserScoreOrm(user_id=USER_ID, score=15, date=today),
        )
        session.add(
            UserScoreOrm(user_id=USER_ID, score=20, date=today - timedelta(days=2)),
        )
        await session.commit()

    async for client in gamification_integration_client_factory(USER_ID):
        current_response = await client.get("/gamification/current-score")
        weekly_response = await client.get("/gamification/weekly-scores")
        period_response = await client.get(
            f"/gamification/period-scores?start_date={(today - timedelta(days=3)).isoformat()}&end_date={today.isoformat()}"
        )

    assert current_response.status_code == 200
    assert current_response.json() == {"score": 15}
    assert weekly_response.status_code == 200
    assert len(weekly_response.json()["scores"]) == 2
    assert period_response.status_code == 200
    assert len(period_response.json()["scores"]) == 2


@pytest.mark.asyncio
async def test_gamification_period_scores_returns_400_for_invalid_period_integration(
    gamification_integration_client_factory,
):
    today = date.today()

    async for client in gamification_integration_client_factory(USER_ID):
        response = await client.get(
            f"/gamification/period-scores?start_date={today.isoformat()}&end_date={(today - timedelta(days=1)).isoformat()}"
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_gamification_praise_returns_expected_streak_title_integration(
    gamification_integration_client_factory,
    gamification_session_factory,
):
    from autotest.integration.gamification.conftest import build_user_orm

    today = date.today()
    async with gamification_session_factory() as session:
        session.add(build_user_orm(USER_ID))
        await session.commit()
        for offset in range(7):
            session.add(UserScoreOrm(user_id=USER_ID, score=30, date=today - timedelta(days=offset)))
        await session.commit()

    async for client in gamification_integration_client_factory(USER_ID):
        response = await client.get("/gamification/praise")

    assert response.status_code == 200
    assert response.json()["consecutive_days"] == 7
    assert response.json()["title"] == "Неделя рядом с собой"


@pytest.mark.asyncio
async def test_gamification_praise_ignores_other_users_scores_integration(
    gamification_integration_client_factory,
    gamification_session_factory,
):
    from autotest.integration.gamification.conftest import build_user_orm

    today = date.today()
    async with gamification_session_factory() as session:
        session.add(build_user_orm(USER_ID))
        session.add(build_user_orm(SECOND_USER_ID))
        await session.commit()
        session.add(UserScoreOrm(user_id=USER_ID, score=30, date=today))
        session.add(UserScoreOrm(user_id=SECOND_USER_ID, score=30, date=today - timedelta(days=1)))
        await session.commit()

    async for client in gamification_integration_client_factory(USER_ID):
        response = await client.get("/gamification/praise")

    assert response.status_code == 200
    assert response.json()["consecutive_days"] == 1


@pytest.mark.asyncio
async def test_gamification_current_score_returns_400_for_invalid_user_id_integration(
    gamification_integration_client_factory,
):
    async for client in gamification_integration_client_factory("not-a-uuid"):
        response = await client.get("/gamification/current-score")

    assert response.status_code == 400
