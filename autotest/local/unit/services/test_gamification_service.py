from datetime import date, timedelta

import pytest

from autotest.factories.gamification import USER_ID
from src.services.gamification import GamificationService


class FakeUserScoreRepository:
    def __init__(self):
        self.current_score_result = 10
        self.weekly_scores_result = [{"date": date.today().isoformat(), "score": 10}]
        self.period_scores_result = [{"date": date.today().isoformat(), "score": 10}]
        self.updated_score_result = 20
        self.fallback_score_result = 7
        self.raise_on_current = None
        self.raise_on_weekly = None
        self.raise_on_period = None
        self.raise_on_update = None
        self.raise_on_archive = None
        self.last_current_user_id = None
        self.last_weekly_user_id = None
        self.last_period_args = None
        self.last_update_args = None
        self.archive_called = False

    async def get_current_score(self, user_id):
        if self.raise_on_current:
            raise self.raise_on_current
        self.last_current_user_id = user_id
        return self.current_score_result

    async def get_weekly_scores(self, user_id):
        if self.raise_on_weekly:
            raise self.raise_on_weekly
        self.last_weekly_user_id = user_id
        return self.weekly_scores_result

    async def get_scores_by_period(self, user_id, start_date, end_date):
        if self.raise_on_period:
            raise self.raise_on_period
        self.last_period_args = (user_id, start_date, end_date)
        return self.period_scores_result

    async def update_current_score(self, user_id, points_to_add):
        if self.raise_on_update:
            raise self.raise_on_update
        self.last_update_args = (user_id, points_to_add)
        return self.updated_score_result

    async def archive_yesterday_scores(self):
        if self.raise_on_archive:
            raise self.raise_on_archive
        self.archive_called = True


class FakeGamificationDb:
    def __init__(self):
        self.user_score = FakeUserScoreRepository()


@pytest.fixture
def fake_gamification_db():
    return FakeGamificationDb()


@pytest.mark.asyncio
async def test_get_current_score_returns_repository_value(fake_gamification_db):
    result = await GamificationService(fake_gamification_db).get_current_score(USER_ID)

    assert result == 10
    assert fake_gamification_db.user_score.last_current_user_id == USER_ID


@pytest.mark.asyncio
async def test_get_current_score_returns_zero_on_error(fake_gamification_db):
    fake_gamification_db.user_score.raise_on_current = RuntimeError("boom")

    result = await GamificationService(fake_gamification_db).get_current_score(USER_ID)

    assert result == 0


@pytest.mark.asyncio
async def test_get_weekly_scores_returns_repository_value(fake_gamification_db):
    result = await GamificationService(fake_gamification_db).get_weekly_scores(USER_ID)

    assert result == [{"date": date.today().isoformat(), "score": 10}]
    assert fake_gamification_db.user_score.last_weekly_user_id == USER_ID


@pytest.mark.asyncio
async def test_get_weekly_scores_returns_empty_list_on_error(fake_gamification_db):
    fake_gamification_db.user_score.raise_on_weekly = RuntimeError("boom")

    result = await GamificationService(fake_gamification_db).get_weekly_scores(USER_ID)

    assert result == []


@pytest.mark.asyncio
async def test_get_scores_by_period_delegates_to_repository(fake_gamification_db):
    start_date = date.today() - timedelta(days=5)
    end_date = date.today()

    result = await GamificationService(fake_gamification_db).get_scores_by_period(USER_ID, start_date, end_date)

    assert result == [{"date": date.today().isoformat(), "score": 10}]
    assert fake_gamification_db.user_score.last_period_args == (USER_ID, start_date, end_date)


@pytest.mark.asyncio
async def test_get_scores_by_period_raises_when_start_date_after_end_date(fake_gamification_db):
    start_date = date.today()
    end_date = date.today() - timedelta(days=1)

    with pytest.raises(ValueError, match="Start date cannot be after end date"):
        await GamificationService(fake_gamification_db).get_scores_by_period(USER_ID, start_date, end_date)


@pytest.mark.asyncio
async def test_get_scores_by_period_raises_when_start_date_in_future(fake_gamification_db):
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=1)

    with pytest.raises(ValueError, match="Start date cannot be in the future"):
        await GamificationService(fake_gamification_db).get_scores_by_period(USER_ID, start_date, end_date)


@pytest.mark.asyncio
async def test_get_scores_by_period_propagates_repository_error(fake_gamification_db):
    start_date = date.today() - timedelta(days=1)
    end_date = date.today()
    fake_gamification_db.user_score.raise_on_period = RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await GamificationService(fake_gamification_db).get_scores_by_period(USER_ID, start_date, end_date)

@pytest.mark.asyncio
async def test_add_points_for_activity_returns_updated_score(fake_gamification_db):
    result = await GamificationService(fake_gamification_db).add_points_for_activity(USER_ID, "theory_read")

    assert result == 20
    assert fake_gamification_db.user_score.last_update_args == (USER_ID, 10)

@pytest.mark.asyncio
async def test_add_points_for_activity_returns_fallback_score_on_error(fake_gamification_db):
    fake_gamification_db.user_score.raise_on_update = RuntimeError("boom")
    fake_gamification_db.user_score.current_score_result = 7

    result = await GamificationService(fake_gamification_db).add_points_for_activity(USER_ID, "theory_read")

    assert result == 7

@pytest.mark.asyncio
async def test_archive_daily_scores_calls_repository(fake_gamification_db):
    await GamificationService(fake_gamification_db).archive_daily_scores()

    assert fake_gamification_db.user_score.archive_called is True

@pytest.mark.asyncio
async def test_archive_daily_scores_propagates_error(fake_gamification_db):
    fake_gamification_db.user_score.raise_on_archive = RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await GamificationService(fake_gamification_db).archive_daily_scores()