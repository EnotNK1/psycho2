import datetime
from types import SimpleNamespace

import pytest

import src.services.mood_tracker as mood_tracker_service_module
from autotest.factories.mood_tracker import (
    MOOD_TRACKER_ID,
    SECOND_MOOD_TRACKER_ID,
    SECOND_USER_ID,
    USER_ID,
    build_add_mood_payload,
    make_emoji,
    make_mood_tracker,
)
from src.exceptions import InvalidEmojiIdException, NotOwnedError, ObjectNotFoundException, ScoreOutOfRangeError
from src.services.mood_tracker import MoodTrackerService


class FakeColumn:
    def __init__(self, name):
        self.name = name

    def __ge__(self, other):
        return (self.name, ">=", other)

    def __le__(self, other):
        return (self.name, "<=", other)


class FakeMoodTrackerRepository:
    def __init__(self):
        self.model = SimpleNamespace(created_at=FakeColumn("created_at"))
        self.filtered_result = []
        self.one_result = None
        self.add_calls = []
        self.get_filtered_calls = []
        self.get_one_calls = []

    async def add(self, data):
        self.add_calls.append(data)

    async def get_filtered(self, *conditions, **filter_by):
        self.get_filtered_calls.append((conditions, filter_by))
        return self.filtered_result

    async def get_one(self, **filter_by):
        self.get_one_calls.append(filter_by)
        return self.one_result


class FakeOntologyRepository:
    def __init__(self):
        self.filtered_result = []
        self.add_calls = []
        self.delete_calls = []

    async def add(self, data):
        self.add_calls.append(data)

    async def get_filtered(self, **filter_by):
        return self.filtered_result

    async def delete(self, **filter_by):
        self.delete_calls.append(filter_by)


class FakeMoodTrackerDb:
    def __init__(self):
        self.mood_tracker = FakeMoodTrackerRepository()
        self.ontology_entry = FakeOntologyRepository()
        self.commit_count = 0

    async def commit(self):
        self.commit_count += 1


class DummyDailyTaskService:
    tasks = []
    complete_calls = []

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.tasks = []
        cls.complete_calls = []

    async def get_daily_tasks(self, user_id):
        return type(self).tasks

    async def complete_daily_task(self, data, user_id):
        type(self).complete_calls.append((data.daily_task_id, user_id))


class DummyGamificationService:
    calls = []

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.calls = []

    async def add_points_for_activity(self, user_id, activity):
        type(self).calls.append((user_id, activity))
        return 10


class DummyEmojiService:
    emoji_map = {}
    calls = []

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.emoji_map = {}
        cls.calls = []

    async def get_emoji_by_id(self, emoji_id):
        type(self).calls.append(emoji_id)
        return type(self).emoji_map.get(emoji_id)


@pytest.fixture
def fake_mood_tracker_db():
    return FakeMoodTrackerDb()


@pytest.fixture(autouse=True)
def reset_mood_tracker_dummies():
    DummyDailyTaskService.reset()
    DummyGamificationService.reset()
    DummyEmojiService.reset()


def make_request(**overrides):
    payload = build_add_mood_payload()
    payload.update(overrides)
    return mood_tracker_service_module.MoodTrackerDateRequestAdd.model_validate(payload)


def test_validate_score_accepts_bounds():
    service = MoodTrackerService()
    service._validate_score(0)
    service._validate_score(100)


def test_validate_score_raises_out_of_range():
    service = MoodTrackerService()

    with pytest.raises(ScoreOutOfRangeError):
        service._validate_score(-1)

    with pytest.raises(ScoreOutOfRangeError):
        service._validate_score(101)


def test_validate_emojis_accepts_valid_ids():
    MoodTrackerService()._validate_emojis([1, 10])


def test_validate_emojis_raises_for_empty_list():
    with pytest.raises(InvalidEmojiIdException):
        MoodTrackerService()._validate_emojis([])


def test_validate_emojis_raises_for_out_of_range_id():
    with pytest.raises(InvalidEmojiIdException):
        MoodTrackerService()._validate_emojis([0, 2])


@pytest.mark.asyncio
async def test_save_mood_tracker_creates_record_completes_daily_tasks_and_commits(fake_mood_tracker_db, monkeypatch):
    DummyDailyTaskService.tasks = [
        {"id": MOOD_TRACKER_ID, "type": 2},
        {"id": SECOND_MOOD_TRACKER_ID, "type": 1},
    ]
    monkeypatch.setattr(mood_tracker_service_module, "DailyTaskService", DummyDailyTaskService)
    monkeypatch.setattr(mood_tracker_service_module, "GamificationService", DummyGamificationService)
    monkeypatch.setattr(mood_tracker_service_module, "recommendations", lambda payload: [])
    monkeypatch.setattr(mood_tracker_service_module, "load_data", lambda path: [])

    await MoodTrackerService(fake_mood_tracker_db).save_mood_tracker(make_request(), USER_ID)

    created = fake_mood_tracker_db.mood_tracker.add_calls[0]
    assert created.score == 55
    assert created.user_id == USER_ID
    assert DummyDailyTaskService.complete_calls == [(MOOD_TRACKER_ID, USER_ID)]
    assert DummyGamificationService.calls == [(USER_ID, "mood_tracker_used")]
    assert fake_mood_tracker_db.commit_count == 1


@pytest.mark.asyncio
async def test_save_mood_tracker_uses_explicit_day_as_created_at(fake_mood_tracker_db, monkeypatch):
    monkeypatch.setattr(mood_tracker_service_module, "DailyTaskService", DummyDailyTaskService)
    monkeypatch.setattr(mood_tracker_service_module, "GamificationService", DummyGamificationService)
    monkeypatch.setattr(mood_tracker_service_module, "recommendations", lambda payload: [])
    monkeypatch.setattr(mood_tracker_service_module, "load_data", lambda path: [])

    await MoodTrackerService(fake_mood_tracker_db).save_mood_tracker(
        make_request(day="2026-04-10"),
        USER_ID,
    )

    assert fake_mood_tracker_db.mood_tracker.add_calls[0].created_at == datetime.datetime(2026, 4, 10, 0, 0, 0)


@pytest.mark.asyncio
async def test_save_mood_tracker_creates_ontology_entries_from_recommendations(fake_mood_tracker_db, monkeypatch):
    monkeypatch.setattr(mood_tracker_service_module, "DailyTaskService", DummyDailyTaskService)
    monkeypatch.setattr(mood_tracker_service_module, "GamificationService", DummyGamificationService)
    material_id = "17171717-1717-1717-1717-171717171717"
    monkeypatch.setattr(
        mood_tracker_service_module,
        "recommendations",
        lambda payload: [{"material_id": material_id, "type": "test"}],
    )
    data_map = {
        "src/services/info/test_info.json": [{"id": material_id, "link": "/images/test.png"}],
        "src/services/info/education_themes.json": [],
        "src/services/info/exercise_info.json": [],
    }
    monkeypatch.setattr(mood_tracker_service_module, "load_data", lambda path: data_map[path])

    await MoodTrackerService(fake_mood_tracker_db).save_mood_tracker(make_request(), USER_ID)

    assert len(fake_mood_tracker_db.ontology_entry.add_calls) == 1
    assert str(fake_mood_tracker_db.ontology_entry.add_calls[0].destination_id) == material_id


@pytest.mark.asyncio
async def test_get_mood_tracker_returns_serialized_records_with_emoji_texts(fake_mood_tracker_db, monkeypatch):
    fake_mood_tracker_db.mood_tracker.filtered_result = [make_mood_tracker()]
    DummyEmojiService.emoji_map = {1: make_emoji(emoji_id=1, text="happy"), 2: make_emoji(emoji_id=2, text="calm")}
    monkeypatch.setattr(mood_tracker_service_module, "EmojiService", DummyEmojiService)

    result = await MoodTrackerService(fake_mood_tracker_db).get_mood_tracker(None, USER_ID)

    assert result[0].id == MOOD_TRACKER_ID
    assert result[0].emoji_texts == ["happy", "calm"]
    assert fake_mood_tracker_db.mood_tracker.get_filtered_calls == [((), {"user_id": USER_ID})]


@pytest.mark.asyncio
async def test_get_mood_tracker_filters_by_day(fake_mood_tracker_db, monkeypatch):
    DummyEmojiService.emoji_map = {}
    monkeypatch.setattr(mood_tracker_service_module, "EmojiService", DummyEmojiService)

    result = await MoodTrackerService(fake_mood_tracker_db).get_mood_tracker("2026-04-15", USER_ID)

    assert result == []
    conditions, filters = fake_mood_tracker_db.mood_tracker.get_filtered_calls[0]
    assert filters == {"user_id": USER_ID}
    assert len(conditions) == 1


@pytest.mark.asyncio
async def test_get_mood_tracker_raises_value_error_for_invalid_day(fake_mood_tracker_db):
    with pytest.raises(ValueError):
        await MoodTrackerService(fake_mood_tracker_db).get_mood_tracker("bad-date", USER_ID)


@pytest.mark.asyncio
async def test_get_weekly_mood_tracker_returns_records(fake_mood_tracker_db, monkeypatch):
    fake_mood_tracker_db.mood_tracker.filtered_result = [make_mood_tracker()]
    DummyEmojiService.emoji_map = {1: make_emoji(emoji_id=1, text="happy"), 2: make_emoji(emoji_id=2, text="calm")}
    monkeypatch.setattr(mood_tracker_service_module, "EmojiService", DummyEmojiService)

    result = await MoodTrackerService(fake_mood_tracker_db).get_weekly_mood_tracker(USER_ID)

    assert result[0].emoji_texts == ["happy", "calm"]
    conditions, filters = fake_mood_tracker_db.mood_tracker.get_filtered_calls[0]
    assert len(conditions) == 2
    assert filters == {"user_id": USER_ID}


@pytest.mark.asyncio
async def test_get_mood_tracker_by_period_returns_records(fake_mood_tracker_db, monkeypatch):
    fake_mood_tracker_db.mood_tracker.filtered_result = [make_mood_tracker(mood_tracker_id=SECOND_MOOD_TRACKER_ID)]
    DummyEmojiService.emoji_map = {1: make_emoji(emoji_id=1, text="happy"), 2: make_emoji(emoji_id=2, text="calm")}
    monkeypatch.setattr(mood_tracker_service_module, "EmojiService", DummyEmojiService)

    result = await MoodTrackerService(fake_mood_tracker_db).get_mood_tracker_by_period(
        USER_ID,
        "2026-04-01",
        "2026-04-15",
    )

    assert result[0].id == SECOND_MOOD_TRACKER_ID
    conditions, filters = fake_mood_tracker_db.mood_tracker.get_filtered_calls[0]
    assert len(conditions) == 2
    assert filters == {"user_id": USER_ID}


@pytest.mark.asyncio
async def test_get_mood_tracker_by_period_raises_value_error_for_invalid_date(fake_mood_tracker_db):
    with pytest.raises(ValueError):
        await MoodTrackerService(fake_mood_tracker_db).get_mood_tracker_by_period(USER_ID, "bad", "2026-04-15")


@pytest.mark.asyncio
async def test_get_mood_tracker_by_id_returns_record_when_owned(fake_mood_tracker_db, monkeypatch):
    fake_mood_tracker_db.mood_tracker.one_result = make_mood_tracker()
    DummyEmojiService.emoji_map = {1: make_emoji(emoji_id=1, text="happy"), 2: make_emoji(emoji_id=2, text="calm")}
    monkeypatch.setattr(mood_tracker_service_module, "EmojiService", DummyEmojiService)

    result = await MoodTrackerService(fake_mood_tracker_db).get_mood_tracker_by_id(MOOD_TRACKER_ID, USER_ID)

    assert result.id == MOOD_TRACKER_ID
    assert result.emoji_texts == ["happy", "calm"]
    assert fake_mood_tracker_db.mood_tracker.get_one_calls == [{"id": MOOD_TRACKER_ID}]


@pytest.mark.asyncio
async def test_get_mood_tracker_by_id_raises_not_owned(fake_mood_tracker_db):
    fake_mood_tracker_db.mood_tracker.one_result = make_mood_tracker(user_id=SECOND_USER_ID)

    with pytest.raises(NotOwnedError):
        await MoodTrackerService(fake_mood_tracker_db).get_mood_tracker_by_id(MOOD_TRACKER_ID, USER_ID)


@pytest.mark.asyncio
async def test_get_mood_tracker_by_id_should_raise_not_found_when_record_missing(fake_mood_tracker_db):
    with pytest.raises(ObjectNotFoundException):
        await MoodTrackerService(fake_mood_tracker_db).get_mood_tracker_by_id(MOOD_TRACKER_ID, USER_ID)
