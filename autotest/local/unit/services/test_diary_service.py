from datetime import datetime
from types import SimpleNamespace

import pytest

from autotest.factories.diary import DIARY_ID, SECOND_DIARY_ID, USER_ID, make_diary
from src.exceptions import (
    FutureDateError,
    InternalErrorHTTPException,
    InvalidDateFormatError,
    InvalidTimestampError,
    TextEmptyError,
    TextTooLongError,
)
from src.services.diary import DiaryService


class FakeColumn:
    def __init__(self, name):
        self.name = name

    def __ge__(self, other):
        return (self.name, ">=", other)

    def __lt__(self, other):
        return (self.name, "<", other)

    def __eq__(self, other):
        return (self.name, "==", other)


class FakeDiaryRepository:
    def __init__(self):
        self.model = SimpleNamespace(user_id=FakeColumn("user_id"), created_at=FakeColumn("created_at"))
        self.add_calls = []
        self.get_filtered_calls = []
        self.filtered_result = []
        self.raise_on_add = None
        self.raise_on_get_filtered = None

    async def add(self, data):
        if self.raise_on_add:
            raise self.raise_on_add
        self.add_calls.append(data)

    async def get_filtered(self, *conditions, **filter_by):
        if self.raise_on_get_filtered:
            raise self.raise_on_get_filtered
        self.get_filtered_calls.append((conditions, filter_by))
        return self.filtered_result


class FakeDiaryDb:
    def __init__(self):
        self.diary = FakeDiaryRepository()
        self.commit_count = 0
        self.raise_on_commit = None

    async def commit(self):
        if self.raise_on_commit:
            raise self.raise_on_commit
        self.commit_count += 1


def make_request(text="Diary note", day="2024-04-15"):
    return SimpleNamespace(text=text, day=day)


def test_validate_text_accepts_normal_text():
    DiaryService()._validate_text("valid note")


def test_validate_text_raises_for_empty_text():
    with pytest.raises(TextEmptyError):
        DiaryService()._validate_text("   ")


def test_validate_text_raises_for_too_long_text():
    with pytest.raises(TextTooLongError):
        DiaryService()._validate_text("x" * 1001)


def test_validate_date_raises_for_future_date():
    with pytest.raises(FutureDateError):
        DiaryService()._validate_date(datetime(2099, 1, 1))


@pytest.mark.asyncio
async def test_add_diary_creates_record_with_explicit_day_and_commits():
    db = FakeDiaryDb()

    await DiaryService(db).add_diary(make_request(day="2024-04-10"), USER_ID)

    created = db.diary.add_calls[0]
    assert created.text == "Diary note"
    assert created.user_id == USER_ID
    assert created.created_at == datetime(2024, 4, 10)
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_add_diary_uses_current_datetime_when_day_missing():
    db = FakeDiaryDb()

    await DiaryService(db).add_diary(make_request(day=None), USER_ID)

    created = db.diary.add_calls[0]
    assert isinstance(created.created_at, datetime)
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_add_diary_raises_for_invalid_date_format():
    db = FakeDiaryDb()

    with pytest.raises(InvalidDateFormatError):
        await DiaryService(db).add_diary(make_request(day="bad-date"), USER_ID)


@pytest.mark.asyncio
async def test_add_diary_raises_for_future_date():
    db = FakeDiaryDb()

    with pytest.raises(FutureDateError):
        await DiaryService(db).add_diary(make_request(day="2099-01-01"), USER_ID)


@pytest.mark.asyncio
async def test_add_diary_raises_for_empty_text():
    db = FakeDiaryDb()

    with pytest.raises(TextEmptyError):
        await DiaryService(db).add_diary(make_request(text="   "), USER_ID)


@pytest.mark.asyncio
async def test_add_diary_raises_for_too_long_text():
    db = FakeDiaryDb()

    with pytest.raises(TextTooLongError):
        await DiaryService(db).add_diary(make_request(text="x" * 1001), USER_ID)


@pytest.mark.asyncio
async def test_add_diary_wraps_repository_error_into_internal_error():
    db = FakeDiaryDb()
    db.diary.raise_on_add = RuntimeError("boom")

    with pytest.raises(InternalErrorHTTPException):
        await DiaryService(db).add_diary(make_request(), USER_ID)


@pytest.mark.asyncio
async def test_add_diary_wraps_commit_error_into_internal_error():
    db = FakeDiaryDb()
    db.raise_on_commit = RuntimeError("boom")

    with pytest.raises(InternalErrorHTTPException):
        await DiaryService(db).add_diary(make_request(), USER_ID)


@pytest.mark.asyncio
async def test_get_diary_returns_all_user_entries():
    db = FakeDiaryDb()
    db.diary.filtered_result = [make_diary(), make_diary(diary_id=SECOND_DIARY_ID, text="Second note")]

    result = await DiaryService(db).get_diary(USER_ID)

    assert len(result) == 2
    conditions, filters = db.diary.get_filtered_calls[0]
    assert len(conditions) == 1
    assert filters == {}


@pytest.mark.asyncio
async def test_get_diary_filters_by_day():
    db = FakeDiaryDb()

    result = await DiaryService(db).get_diary(USER_ID, "2026-04-15")

    assert result == []
    conditions, filters = db.diary.get_filtered_calls[0]
    assert len(conditions) == 2
    assert filters == {}


@pytest.mark.asyncio
async def test_get_diary_raises_for_invalid_date_format():
    db = FakeDiaryDb()

    with pytest.raises(InvalidDateFormatError):
        await DiaryService(db).get_diary(USER_ID, "bad-date")


@pytest.mark.asyncio
async def test_get_diary_returns_empty_list():
    db = FakeDiaryDb()

    result = await DiaryService(db).get_diary(USER_ID)

    assert result == []


@pytest.mark.asyncio
async def test_get_diary_for_month_returns_days_with_diary_flags():
    db = FakeDiaryDb()
    db.diary.filtered_result = [
        make_diary(diary_id=DIARY_ID, created_at=datetime(2026, 4, 2, 10, 0, 0)),
        make_diary(diary_id=SECOND_DIARY_ID, created_at=datetime(2026, 4, 10, 12, 0, 0)),
    ]

    result = await DiaryService(db).get_diary_for_month(1775001600, USER_ID)

    assert len(result) == 30
    assert result[1]["diary"] is True
    assert result[9]["diary"] is True
    assert result[0]["diary"] is False
    conditions, filters = db.diary.get_filtered_calls[0]
    assert len(conditions) == 2
    assert filters == {"user_id": USER_ID}


@pytest.mark.asyncio
async def test_get_diary_for_month_returns_all_false_for_empty_month():
    db = FakeDiaryDb()

    result = await DiaryService(db).get_diary_for_month(1775001600, USER_ID)

    assert len(result) == 30
    assert all(item["diary"] is False for item in result)


@pytest.mark.asyncio
async def test_get_diary_for_month_raises_for_invalid_timestamp():
    db = FakeDiaryDb()

    with pytest.raises(InvalidTimestampError):
        await DiaryService(db).get_diary_for_month(0, USER_ID)


@pytest.mark.asyncio
async def test_get_diary_for_month_wraps_repository_error_into_internal_error():
    db = FakeDiaryDb()
    db.diary.raise_on_get_filtered = RuntimeError("boom")

    with pytest.raises(InternalErrorHTTPException):
        await DiaryService(db).get_diary_for_month(1775001600, USER_ID)
