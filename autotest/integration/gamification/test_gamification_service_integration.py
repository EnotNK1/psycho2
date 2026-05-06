from datetime import date, timedelta

import pytest
from sqlalchemy import select

from autotest.factories.gamification import USER_ID
from src.models.gamification import UserScoreOrm
from src.services.gamification import GamificationService


@pytest.mark.asyncio
async def test_gamification_service_get_current_score_returns_real_value(
    gamification_db,
    gamification_session_factory,
):
    from autotest.integration.gamification.conftest import build_user_orm

    today = date.today()
    async with gamification_session_factory() as session:
        session.add(build_user_orm(USER_ID))
        await session.commit()
        session.add(UserScoreOrm(user_id=USER_ID, score=12, date=today))
        await session.commit()

    result = await GamificationService(gamification_db).get_current_score(USER_ID)

    assert result == 12


@pytest.mark.asyncio
async def test_gamification_service_get_weekly_scores_returns_real_rows(
    gamification_db,
    gamification_session_factory,
):
    from autotest.integration.gamification.conftest import build_user_orm

    today = date.today()
    async with gamification_session_factory() as session:
        session.add(build_user_orm(USER_ID))
        await session.commit()
        session.add(UserScoreOrm(user_id=USER_ID, score=10, date=today))
        session.add(UserScoreOrm(user_id=USER_ID, score=20, date=today - timedelta(days=2)))
        await session.commit()

    result = await GamificationService(gamification_db).get_weekly_scores(USER_ID)

    assert len(result) == 2
    assert result[0]["score"] in {10, 20}


@pytest.mark.asyncio
async def test_gamification_service_get_scores_by_period_returns_real_rows(
    gamification_db,
    gamification_session_factory,
):
    from autotest.integration.gamification.conftest import build_user_orm

    today = date.today()
    async with gamification_session_factory() as session:
        session.add(build_user_orm(USER_ID))
        await session.commit()
        session.add(UserScoreOrm(user_id=USER_ID, score=10, date=today))
        session.add(UserScoreOrm(user_id=USER_ID, score=20, date=today - timedelta(days=2)))
        await session.commit()

    result = await GamificationService(gamification_db).get_scores_by_period(
        USER_ID,
        today - timedelta(days=3),
        today,
    )

    assert len(result) == 2


@pytest.mark.asyncio
async def test_gamification_service_add_points_for_activity_creates_today_row(
    gamification_db,
    gamification_session_factory,
):
    from autotest.integration.gamification.conftest import build_user_orm

    today = date.today()
    async with gamification_session_factory() as session:
        session.add(build_user_orm(USER_ID))
        await session.commit()

    result = await GamificationService(gamification_db).add_points_for_activity(USER_ID, "theory_read")

    assert result == 10

    async with gamification_session_factory() as session:
        rows = (
            await session.execute(
                select(UserScoreOrm).where(UserScoreOrm.user_id == USER_ID, UserScoreOrm.date == today)
            )
        ).scalars().all()
    assert len(rows) == 1
    assert rows[0].score == 10


@pytest.mark.asyncio
async def test_gamification_service_add_points_for_activity_caps_score_at_40(
    gamification_db,
    gamification_session_factory,
):
    from autotest.integration.gamification.conftest import build_user_orm

    today = date.today()
    async with gamification_session_factory() as session:
        session.add(build_user_orm(USER_ID))
        await session.commit()
        session.add(UserScoreOrm(user_id=USER_ID, score=35, date=today))
        await session.commit()

    result = await GamificationService(gamification_db).add_points_for_activity(USER_ID, "theory_read")

    assert result == 40


@pytest.mark.asyncio
async def test_gamification_service_get_scores_by_period_raises_for_invalid_period(
    gamification_db,
):
    today = date.today()

    with pytest.raises(ValueError, match="Start date cannot be after end date"):
        await GamificationService(gamification_db).get_scores_by_period(USER_ID, today, today - timedelta(days=1))
