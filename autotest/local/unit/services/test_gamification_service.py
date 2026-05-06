from datetime import date, timedelta
from types import SimpleNamespace
import uuid

import pytest

import src.services.gamification as gamification_service_module
from src.services.gamification import GamificationService


USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


class FakeDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 4, 20)


class FakeUserScoreRepository:
    def __init__(self):
        self.score_by_date = {}
        self.get_by_user_and_date_calls = []
        self.get_scores_by_period_calls = []
        self.create_calls = []
        self.update_calls = []

    async def get_by_user_and_date(self, user_id, target_date):
        self.get_by_user_and_date_calls.append((user_id, target_date))
        return self.score_by_date.get(target_date)

    async def get_scores_by_period(self, user_id, start_date, end_date):
        self.get_scores_by_period_calls.append((user_id, start_date, end_date))
        return [
            score
            for score_date, score in sorted(self.score_by_date.items())
            if start_date <= score_date <= end_date
        ]

    async def create(self, user_id, score, target_date):
        record = SimpleNamespace(user_id=user_id, score=score, date=target_date)
        self.score_by_date[target_date] = record
        self.create_calls.append((user_id, score, target_date))
        return record

    async def update_score(self, score_record, new_score):
        score_record.score = new_score
        self.update_calls.append((score_record.date, new_score))
        return score_record

    async def archive_yesterday_scores(self):
        return None


class FakeDb:
    def __init__(self):
        self.user_score = FakeUserScoreRepository()


@pytest.fixture
def fake_db(monkeypatch):
    monkeypatch.setattr(gamification_service_module, "date", FakeDate)
    return FakeDb()


def make_score(score_date: date, score: int):
    return SimpleNamespace(date=score_date, score=score)


@pytest.mark.asyncio
async def test_add_points_for_activity_creates_daily_record(fake_db):
    service = GamificationService(fake_db)

    new_score = await service.add_points_for_activity(USER_ID, "test_completed")

    assert new_score == 10
    assert fake_db.user_score.create_calls == [(USER_ID, 10, FakeDate.today())]


@pytest.mark.asyncio
async def test_add_points_for_activity_respects_daily_cap(fake_db):
    fake_db.user_score.score_by_date[FakeDate.today()] = make_score(FakeDate.today(), 35)
    service = GamificationService(fake_db)

    new_score = await service.add_points_for_activity(USER_ID, "mood_tracker_used")

    assert new_score == 40
    assert fake_db.user_score.update_calls == [(FakeDate.today(), 40)]


@pytest.mark.asyncio
async def test_get_weekly_scores_uses_service_period_window(fake_db):
    for days_ago, score in ((6, 10), (2, 20), (0, 30)):
        score_date = FakeDate.today() - timedelta(days=days_ago)
        fake_db.user_score.score_by_date[score_date] = make_score(score_date, score)

    service = GamificationService(fake_db)
    scores = await service.get_weekly_scores(str(USER_ID))

    assert fake_db.user_score.get_scores_by_period_calls == [
        (USER_ID, FakeDate.today() - timedelta(days=6), FakeDate.today())
    ]
    assert scores == [
        {"date": "2026-04-14", "score": 10},
        {"date": "2026-04-15", "score": 0},
        {"date": "2026-04-16", "score": 0},
        {"date": "2026-04-17", "score": 0},
        {"date": "2026-04-18", "score": 20},
        {"date": "2026-04-19", "score": 0},
        {"date": "2026-04-20", "score": 30},
    ]


@pytest.mark.asyncio
async def test_get_weekly_scores_returns_seven_zero_days_when_no_scores(fake_db):
    service = GamificationService(fake_db)

    scores = await service.get_weekly_scores(USER_ID)

    assert scores == [
        {"date": "2026-04-14", "score": 0},
        {"date": "2026-04-15", "score": 0},
        {"date": "2026-04-16", "score": 0},
        {"date": "2026-04-17", "score": 0},
        {"date": "2026-04-18", "score": 0},
        {"date": "2026-04-19", "score": 0},
        {"date": "2026-04-20", "score": 0},
    ]


@pytest.mark.asyncio
async def test_get_scores_by_period_validates_dates(fake_db):
    service = GamificationService(fake_db)

    with pytest.raises(ValueError, match="Start date cannot be after end date"):
        await service.get_scores_by_period(
            USER_ID, FakeDate.today(), FakeDate.today() - timedelta(days=1)
        )


@pytest.mark.asyncio
async def test_get_scores_by_period_fills_missing_days_with_zero(fake_db):
    fake_db.user_score.score_by_date[FakeDate(2026, 4, 18)] = make_score(
        FakeDate(2026, 4, 18), 20
    )
    fake_db.user_score.score_by_date[FakeDate(2026, 4, 20)] = make_score(
        FakeDate(2026, 4, 20), 30
    )
    service = GamificationService(fake_db)

    scores = await service.get_scores_by_period(
        USER_ID, FakeDate(2026, 4, 17), FakeDate(2026, 4, 20)
    )

    assert scores == [
        {"date": "2026-04-17", "score": 0},
        {"date": "2026-04-18", "score": 20},
        {"date": "2026-04-19", "score": 0},
        {"date": "2026-04-20", "score": 30},
    ]


@pytest.mark.asyncio
async def test_get_praise_returns_title_for_three_day_streak(fake_db):
    for days_ago in range(3):
        score_date = FakeDate.today() - timedelta(days=days_ago)
        fake_db.user_score.score_by_date[score_date] = make_score(score_date, 30)

    service = GamificationService(fake_db)
    praise = await service.get_praise(USER_ID)

    assert praise == {
        "consecutive_days": 3,
        "title": "Ты на верном пути",
        "subtitle": "Мы рады тебе! Продолжай в своем темпе",
    }


@pytest.mark.asyncio
async def test_get_praise_stops_on_gap_or_low_score(fake_db):
    fake_db.user_score.score_by_date[FakeDate.today()] = make_score(FakeDate.today(), 30)
    fake_db.user_score.score_by_date[FakeDate.today() - timedelta(days=1)] = make_score(
        FakeDate.today() - timedelta(days=1), 10
    )

    service = GamificationService(fake_db)
    praise = await service.get_praise(USER_ID)

    assert praise == {
        "consecutive_days": 1,
        "title": "",
        "subtitle": "",
    }
