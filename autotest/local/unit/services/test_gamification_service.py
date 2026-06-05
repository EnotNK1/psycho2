from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from autotest.factories.gamification import USER_ID
from src.services.gamification import GamificationService


def make_score(score_date, score):
    return SimpleNamespace(date=score_date, score=score)


class FakeUserScoreRepository:
    def __init__(self):
        self.raise_on_get_by_date = None
        self.raise_on_period = None
        self.raise_on_update = None
        self.raise_on_create = None
        self.raise_on_archive = None
        self.score_by_date = {}
        self.period_scores_result = []
        self.last_get_by_date_args = None
        self.last_period_args = None
        self.last_update_args = None
        self.last_create_args = None
        self.archive_called = False

    async def get_by_user_and_date(self, user_id, target_date):
        if self.raise_on_get_by_date:
            raise self.raise_on_get_by_date
        self.last_get_by_date_args = (user_id, target_date)
        return self.score_by_date.get((user_id, target_date))

    async def get_scores_by_period(self, user_id, start_date, end_date):
        if self.raise_on_period:
            raise self.raise_on_period
        self.last_period_args = (user_id, start_date, end_date)
        return self.period_scores_result

    async def update_score(self, score_record, new_score):
        if self.raise_on_update:
            raise self.raise_on_update
        self.last_update_args = (score_record, new_score)
        score_record.score = new_score

    async def create(self, user_id, score, target_date):
        if self.raise_on_create:
            raise self.raise_on_create
        self.last_create_args = (user_id, score, target_date)
        self.score_by_date[(user_id, target_date)] = make_score(target_date, score)

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
async def test_get_current_score_returns_today_score_and_normalizes_user_id(fake_gamification_db):
    today = date.today()
    fake_gamification_db.user_score.score_by_date[(USER_ID, today)] = make_score(today, 12)

    result = await GamificationService(fake_gamification_db).get_current_score(str(USER_ID))

    assert result == 12
    assert fake_gamification_db.user_score.last_get_by_date_args == (USER_ID, today)


@pytest.mark.asyncio
async def test_get_current_score_returns_zero_when_record_missing(fake_gamification_db):
    result = await GamificationService(fake_gamification_db).get_current_score(USER_ID)

    assert result == 0


@pytest.mark.asyncio
async def test_get_current_score_returns_zero_on_error(fake_gamification_db):
    fake_gamification_db.user_score.raise_on_get_by_date = RuntimeError("boom")

    result = await GamificationService(fake_gamification_db).get_current_score(USER_ID)

    assert result == 0


@pytest.mark.asyncio
async def test_get_weekly_scores_returns_dense_seven_day_payload(fake_gamification_db):
    today = date.today()
    fake_gamification_db.user_score.period_scores_result = [
        make_score(today - timedelta(days=2), 15),
        make_score(today, 25),
    ]

    result = await GamificationService(fake_gamification_db).get_weekly_scores(USER_ID)

    assert len(result) == 7
    assert result[-1] == {"date": today.isoformat(), "score": 25}
    assert result[-3] == {"date": (today - timedelta(days=2)).isoformat(), "score": 15}
    assert result[0]["score"] == 0
    assert fake_gamification_db.user_score.last_period_args == (
        USER_ID,
        today - timedelta(days=6),
        today,
    )


@pytest.mark.asyncio
async def test_get_weekly_scores_returns_empty_list_on_error(fake_gamification_db):
    fake_gamification_db.user_score.raise_on_period = RuntimeError("boom")

    result = await GamificationService(fake_gamification_db).get_weekly_scores(USER_ID)

    assert result == []


@pytest.mark.asyncio
async def test_get_scores_by_period_returns_dense_payload(fake_gamification_db):
    start_date = date.today() - timedelta(days=2)
    end_date = date.today()
    fake_gamification_db.user_score.period_scores_result = [
        make_score(start_date, 5),
        make_score(end_date, 20),
    ]

    result = await GamificationService(fake_gamification_db).get_scores_by_period(USER_ID, start_date, end_date)

    assert result == [
        {"date": start_date.isoformat(), "score": 5},
        {"date": (start_date + timedelta(days=1)).isoformat(), "score": 0},
        {"date": end_date.isoformat(), "score": 20},
    ]
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
async def test_add_points_for_activity_updates_existing_score_with_cap(fake_gamification_db):
    today = date.today()
    existing_score = make_score(today, 35)
    fake_gamification_db.user_score.score_by_date[(USER_ID, today)] = existing_score

    result = await GamificationService(fake_gamification_db).add_points_for_activity(USER_ID, "theory_read")

    assert result == 40
    assert fake_gamification_db.user_score.last_update_args == (existing_score, 40)
    assert fake_gamification_db.user_score.last_create_args is None


@pytest.mark.asyncio
async def test_add_points_for_activity_creates_new_score_for_today(fake_gamification_db):
    today = date.today()

    result = await GamificationService(fake_gamification_db).add_points_for_activity(USER_ID, "theory_read")

    assert result == 10
    assert fake_gamification_db.user_score.last_create_args == (USER_ID, 10, today)
    assert fake_gamification_db.user_score.score_by_date[(USER_ID, today)].score == 10


@pytest.mark.asyncio
async def test_add_points_for_activity_returns_fallback_score_on_error(fake_gamification_db):
    today = date.today()
    existing_score = make_score(today, 7)
    fake_gamification_db.user_score.score_by_date[(USER_ID, today)] = existing_score
    fake_gamification_db.user_score.raise_on_update = RuntimeError("boom")

    result = await GamificationService(fake_gamification_db).add_points_for_activity(USER_ID, "theory_read")

    assert result == 7


@pytest.mark.asyncio
async def test_get_praise_returns_blank_payload_when_scores_missing(fake_gamification_db):
    result = await GamificationService(fake_gamification_db).get_praise(USER_ID)

    assert result == {"consecutive_days": 0, "title": "", "subtitle": ""}


@pytest.mark.asyncio
async def test_get_praise_returns_expected_payload_for_seven_day_streak(fake_gamification_db):
    today = date.today()
    fake_gamification_db.user_score.period_scores_result = [
        make_score(today - timedelta(days=offset), 30)
        for offset in range(7)
    ]

    result = await GamificationService(fake_gamification_db).get_praise(USER_ID)

    assert result["consecutive_days"] == 7
    assert result == GamificationService._build_praise(7)


@pytest.mark.asyncio
async def test_get_praise_breaks_streak_when_score_not_above_threshold(fake_gamification_db):
    today = date.today()
    fake_gamification_db.user_score.period_scores_result = [
        make_score(today - timedelta(days=2), 30),
        make_score(today - timedelta(days=1), 30),
        make_score(today, 20),
    ]

    result = await GamificationService(fake_gamification_db).get_praise(USER_ID)

    assert result == {"consecutive_days": 0, "title": "", "subtitle": ""}


@pytest.mark.asyncio
async def test_get_praise_breaks_streak_on_gap_between_dates(fake_gamification_db):
    today = date.today()
    fake_gamification_db.user_score.period_scores_result = [
        make_score(today - timedelta(days=3), 30),
        make_score(today - timedelta(days=1), 30),
        make_score(today, 30),
    ]

    result = await GamificationService(fake_gamification_db).get_praise(USER_ID)

    assert result["consecutive_days"] == 2
    assert result == {"consecutive_days": 2, "title": "", "subtitle": ""}


@pytest.mark.asyncio
async def test_archive_daily_scores_calls_repository(fake_gamification_db):
    await GamificationService(fake_gamification_db).archive_daily_scores()

    assert fake_gamification_db.user_score.archive_called is True


@pytest.mark.asyncio
async def test_archive_daily_scores_propagates_error(fake_gamification_db):
    fake_gamification_db.user_score.raise_on_archive = RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await GamificationService(fake_gamification_db).archive_daily_scores()
