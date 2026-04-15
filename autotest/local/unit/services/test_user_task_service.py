from datetime import datetime, timedelta

import pytest

from autotest4.factories.user_task import OTHER_TASK_ID, TASK_ID, USER_ID, make_task
from src.exceptions import DateException, InternalErrorHTTPException, TextEmptyError, TextTooLongError
from src.services.user_task import UserTaskService
from types import SimpleNamespace


class FakeScalarResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return list(self._items)


class FakeExecuteResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return FakeScalarResult(self._items)


class FakeUserTaskRepository:
    def __init__(self):
        self.filtered_result = []
        self.get_one_result = None
        self.get_filtered_calls = []
        self.get_one_calls = []
        self.add_calls = []
        self.edit_calls = []
        self.delete_calls = []
        self.raise_on_add = None
        self.raise_on_get_one = None
        self.raise_on_edit = None
        self.raise_on_delete = None

    async def add(self, data):
        if self.raise_on_add:
            raise self.raise_on_add
        self.add_calls.append(data)

    async def get_one(self, **filter_by):
        if self.raise_on_get_one:
            raise self.raise_on_get_one
        self.get_one_calls.append(filter_by)
        return self.get_one_result

    async def edit(self, **kwargs):
        if self.raise_on_edit:
            raise self.raise_on_edit
        self.edit_calls.append(kwargs)

    async def get_filtered(self, **filter_by):
        self.get_filtered_calls.append(filter_by)
        return self.filtered_result

    async def delete(self, **filter_by):
        if self.raise_on_delete:
            raise self.raise_on_delete
        self.delete_calls.append(filter_by)


class FakeUserTaskDb:
    def __init__(self):
        self.user_task = FakeUserTaskRepository()
        self.commit_count = 0
        self.commit_should_raise = None
        self.execute_items = []
        self.execute_should_raise = None

    async def commit(self):
        if self.commit_should_raise:
            raise self.commit_should_raise
        self.commit_count += 1

    async def execute(self, query):
        if self.execute_should_raise:
            raise self.execute_should_raise
        return FakeExecuteResult(self.execute_items)


@pytest.fixture
def fake_user_task_db():
    return FakeUserTaskDb()


@pytest.mark.asyncio
async def test_service_add_user_task_creates_and_commits(fake_user_task_db, monkeypatch):
    fixed_now = datetime(2026, 4, 10, 12, 30, 0)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr("src.services.user_task.datetime", FixedDatetime)

    data = SimpleNamespace(text="New task")
    await UserTaskService(fake_user_task_db).add_user_task(data, USER_ID)

    assert len(fake_user_task_db.user_task.add_calls) == 1
    created = fake_user_task_db.user_task.add_calls[0]
    assert created.text == "New task"
    assert created.created_at == fixed_now
    assert created.is_complete is False
    assert created.user_id == USER_ID
    assert fake_user_task_db.commit_count == 1


@pytest.mark.asyncio
async def test_service_add_user_task_wraps_commit_error(fake_user_task_db):
    fake_user_task_db.commit_should_raise = RuntimeError("commit failed")

    with pytest.raises(InternalErrorHTTPException):
        await UserTaskService(fake_user_task_db).add_user_task(SimpleNamespace(text="Task"), USER_ID)


@pytest.mark.asyncio
async def test_service_add_user_task_reraises_text_empty_error(fake_user_task_db):
    fake_user_task_db.user_task.raise_on_add = TextEmptyError()

    with pytest.raises(TextEmptyError):
        await UserTaskService(fake_user_task_db).add_user_task(SimpleNamespace(text=""), USER_ID)


@pytest.mark.asyncio
async def test_service_add_user_task_reraises_text_too_long_error(fake_user_task_db):
    fake_user_task_db.user_task.raise_on_add = TextTooLongError()

    with pytest.raises(TextTooLongError):
        await UserTaskService(fake_user_task_db).add_user_task(SimpleNamespace(text="x"), USER_ID)


@pytest.mark.asyncio
async def test_service_add_user_task_wraps_unexpected_error(fake_user_task_db):
    fake_user_task_db.user_task.raise_on_add = RuntimeError("boom")

    with pytest.raises(InternalErrorHTTPException):
        await UserTaskService(fake_user_task_db).add_user_task(SimpleNamespace(text="Task"), USER_ID)


@pytest.mark.asyncio
async def test_service_update_user_task_updates_text_only(fake_user_task_db):
    fake_user_task_db.user_task.get_one_result = make_task(completed_at=datetime(2026, 4, 1, 12, 0, 0))
    data = SimpleNamespace(user_task_id=TASK_ID, text="Updated", is_complete=None)

    await UserTaskService(fake_user_task_db).update_user_task(data)

    edit_call = fake_user_task_db.user_task.edit_calls[0]
    assert edit_call["id"] == TASK_ID
    assert edit_call["exclude_unset"] is True
    assert edit_call["data"].text == "Updated"
    assert fake_user_task_db.commit_count == 1


@pytest.mark.asyncio
async def test_service_update_user_task_updates_completion_true_and_sets_completed_at(
    fake_user_task_db,
    monkeypatch,
):
    fixed_now = datetime(2026, 4, 10, 18, 0, 0)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr("src.services.user_task.datetime", FixedDatetime)
    fake_user_task_db.user_task.get_one_result = make_task(completed_at=None)
    data = SimpleNamespace(user_task_id=TASK_ID, text=None, is_complete=True)

    await UserTaskService(fake_user_task_db).update_user_task(data)

    edit_call = fake_user_task_db.user_task.edit_calls[0]
    assert edit_call["data"].is_complete is True
    assert edit_call["data"].completed_at == fixed_now


@pytest.mark.asyncio
async def test_service_update_user_task_updates_completion_false_and_clears_completed_at(fake_user_task_db):
    fake_user_task_db.user_task.get_one_result = make_task(completed_at=datetime(2026, 4, 10, 10, 0, 0))
    data = SimpleNamespace(user_task_id=TASK_ID, text=None, is_complete=False)

    await UserTaskService(fake_user_task_db).update_user_task(data)

    edit_call = fake_user_task_db.user_task.edit_calls[0]
    assert edit_call["data"].is_complete is False
    assert edit_call["data"].completed_at is None


@pytest.mark.asyncio
async def test_service_update_user_task_updates_text_and_completion(fake_user_task_db, monkeypatch):
    fixed_now = datetime(2026, 4, 10, 19, 0, 0)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr("src.services.user_task.datetime", FixedDatetime)
    fake_user_task_db.user_task.get_one_result = make_task()
    data = SimpleNamespace(user_task_id=TASK_ID, text="Done", is_complete=True)

    await UserTaskService(fake_user_task_db).update_user_task(data)

    edit_call = fake_user_task_db.user_task.edit_calls[0]
    assert edit_call["data"].text == "Done"
    assert edit_call["data"].is_complete is True
    assert edit_call["data"].completed_at == fixed_now


@pytest.mark.asyncio
async def test_service_update_user_task_with_no_optional_fields_keeps_completion_timestamp(fake_user_task_db):
    existing_completed_at = datetime(2026, 4, 10, 8, 0, 0)
    fake_user_task_db.user_task.get_one_result = make_task(completed_at=existing_completed_at)

    await UserTaskService(fake_user_task_db).update_user_task(
        SimpleNamespace(user_task_id=TASK_ID, text=None, is_complete=None)
    )

    edit_call = fake_user_task_db.user_task.edit_calls[0]
    assert edit_call["data"].text is None
    assert fake_user_task_db.commit_count == 1


@pytest.mark.asyncio
async def test_service_update_user_task_reraises_text_empty_error(fake_user_task_db):
    fake_user_task_db.user_task.raise_on_get_one = TextEmptyError()

    with pytest.raises(TextEmptyError):
        await UserTaskService(fake_user_task_db).update_user_task(
            SimpleNamespace(user_task_id=TASK_ID, text="", is_complete=None)
        )


@pytest.mark.asyncio
async def test_service_update_user_task_reraises_text_too_long_error(fake_user_task_db):
    fake_user_task_db.user_task.raise_on_edit = TextTooLongError()
    fake_user_task_db.user_task.get_one_result = make_task()

    with pytest.raises(TextTooLongError):
        await UserTaskService(fake_user_task_db).update_user_task(
            SimpleNamespace(user_task_id=TASK_ID, text="x", is_complete=None)
        )


@pytest.mark.asyncio
async def test_service_update_user_task_wraps_unexpected_error(fake_user_task_db):
    fake_user_task_db.user_task.raise_on_get_one = RuntimeError("boom")

    with pytest.raises(InternalErrorHTTPException):
        await UserTaskService(fake_user_task_db).update_user_task(
            SimpleNamespace(user_task_id=TASK_ID, text="Task", is_complete=None)
        )


@pytest.mark.asyncio
async def test_service_update_user_task_wraps_commit_error(fake_user_task_db):
    fake_user_task_db.user_task.get_one_result = make_task()
    fake_user_task_db.commit_should_raise = RuntimeError("commit failed")

    with pytest.raises(InternalErrorHTTPException):
        await UserTaskService(fake_user_task_db).update_user_task(
            SimpleNamespace(user_task_id=TASK_ID, text="Task", is_complete=None)
        )


@pytest.mark.asyncio
async def test_service_get_actual_user_tasks_returns_incomplete_tasks(fake_user_task_db):
    fake_user_task_db.user_task.filtered_result = [
        make_task(text="Task 1", is_complete=False),
        make_task(task_id=OTHER_TASK_ID, text="Task 2", is_complete=False),
    ]

    result = await UserTaskService(fake_user_task_db).get_actual_user_tasks(USER_ID, None)

    assert [item["id"] for item in result] == [str(TASK_ID), str(OTHER_TASK_ID)]
    assert fake_user_task_db.user_task.get_filtered_calls == [{"user_id": USER_ID, "is_complete": False}]


@pytest.mark.asyncio
async def test_service_get_actual_user_tasks_returns_empty_list_when_repository_is_empty(fake_user_task_db):
    result = await UserTaskService(fake_user_task_db).get_actual_user_tasks(USER_ID, None)

    assert result == []


@pytest.mark.asyncio
async def test_service_get_actual_user_tasks_merges_incomplete_and_daily_tasks_without_duplicates(
    fake_user_task_db,
):
    common_task = make_task(task_id=TASK_ID, text="Task 1")
    day_only_task = make_task(task_id=OTHER_TASK_ID, text="Task 2")
    fake_user_task_db.user_task.filtered_result = [common_task]
    fake_user_task_db.execute_items = [common_task, day_only_task]

    result = await UserTaskService(fake_user_task_db).get_actual_user_tasks(
        USER_ID,
        datetime(2026, 4, 10, 15, 0, 0),
    )

    assert len(result) == 2
    assert {item["id"] for item in result} == {str(TASK_ID), str(OTHER_TASK_ID)}


@pytest.mark.asyncio
async def test_service_get_actual_user_tasks_returns_empty_list_on_execute_error(fake_user_task_db):
    fake_user_task_db.execute_should_raise = RuntimeError("db failed")

    result = await UserTaskService(fake_user_task_db).get_actual_user_tasks(
        USER_ID,
        datetime(2026, 4, 10, 15, 0, 0),
    )

    assert result == []


@pytest.mark.asyncio
async def test_service_get_completed_user_tasks_raises_when_only_start_date_provided(fake_user_task_db):
    with pytest.raises(DateException):
        await UserTaskService(fake_user_task_db).get_completed_user_tasks(USER_ID, datetime(2026, 4, 1).date(), None)


@pytest.mark.asyncio
async def test_service_get_completed_user_tasks_raises_when_only_end_date_provided(fake_user_task_db):
    with pytest.raises(DateException):
        await UserTaskService(fake_user_task_db).get_completed_user_tasks(USER_ID, None, datetime(2026, 4, 10).date())


@pytest.mark.asyncio
async def test_service_get_completed_user_tasks_uses_default_range_and_sorts_desc(fake_user_task_db, monkeypatch):
    base_now = datetime(2026, 4, 10, 12, 0, 0)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return base_now

    monkeypatch.setattr("src.services.user_task.datetime", FixedDatetime)
    older = make_task(
        task_id=TASK_ID,
        text="Older",
        created_at=base_now - timedelta(days=3),
        completed_at=base_now - timedelta(days=3),
        is_complete=True,
    )
    newer = make_task(
        task_id=OTHER_TASK_ID,
        text="Newer",
        created_at=base_now - timedelta(days=1),
        completed_at=base_now - timedelta(days=1),
        is_complete=True,
    )
    fake_user_task_db.execute_items = [older, newer]

    result = await UserTaskService(fake_user_task_db).get_completed_user_tasks(USER_ID)

    assert [item["text"] for item in result] == ["Newer", "Older"]


@pytest.mark.asyncio
async def test_service_get_completed_user_tasks_accepts_explicit_date_range(fake_user_task_db):
    task = make_task(
        task_id=TASK_ID,
        text="Done",
        created_at=datetime(2026, 4, 5, 10, 0, 0),
        completed_at=datetime(2026, 4, 5, 11, 0, 0),
        is_complete=True,
    )
    fake_user_task_db.execute_items = [task]

    result = await UserTaskService(fake_user_task_db).get_completed_user_tasks(
        USER_ID,
        datetime(2026, 4, 1).date(),
        datetime(2026, 4, 10).date(),
    )

    assert result == [
        {
            "id": str(TASK_ID),
            "text": "Done",
            "created_at": "2026-04-05T10:00:00",
            "completed_at": "2026-04-05T11:00:00",
            "is_complete": True,
            "user_id": str(USER_ID),
        }
    ]


@pytest.mark.asyncio
async def test_service_get_completed_user_tasks_returns_empty_list_when_query_is_empty(fake_user_task_db):
    result = await UserTaskService(fake_user_task_db).get_completed_user_tasks(
        USER_ID,
        datetime(2026, 4, 1).date(),
        datetime(2026, 4, 10).date(),
    )

    assert result == []


@pytest.mark.asyncio
async def test_service_get_completed_user_tasks_returns_empty_list_on_execute_error(fake_user_task_db):
    fake_user_task_db.execute_should_raise = RuntimeError("db failed")

    result = await UserTaskService(fake_user_task_db).get_completed_user_tasks(
        USER_ID,
        datetime(2026, 4, 1).date(),
        datetime(2026, 4, 10).date(),
    )

    assert result == []


@pytest.mark.asyncio
async def test_service_delete_calls_repository_and_commits(fake_user_task_db):
    result = await UserTaskService(fake_user_task_db).delete(SimpleNamespace(user_task_id=TASK_ID))

    assert result == {"status": "OK"}
    assert fake_user_task_db.user_task.delete_calls == [{"id": TASK_ID}]
    assert fake_user_task_db.commit_count == 1


@pytest.mark.asyncio
async def test_service_delete_wraps_repository_error(fake_user_task_db):
    fake_user_task_db.user_task.raise_on_delete = RuntimeError("boom")

    with pytest.raises(InternalErrorHTTPException):
        await UserTaskService(fake_user_task_db).delete(SimpleNamespace(user_task_id=TASK_ID))


@pytest.mark.asyncio
async def test_service_delete_wraps_commit_error(fake_user_task_db):
    fake_user_task_db.commit_should_raise = RuntimeError("commit failed")

    with pytest.raises(InternalErrorHTTPException):
        await UserTaskService(fake_user_task_db).delete(SimpleNamespace(user_task_id=TASK_ID))
