from datetime import datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

import src.api.admin as admin_api_module
from src.api.dependencies.admin import verify_admin
from src.api.dependencies.db import get_db


ADMIN_ID = uuid4()
USER_ID = uuid4()
SECOND_USER_ID = uuid4()
TEST_RESULT_ID = uuid4()
TEST_ID = uuid4()
COMPLETED_EXERCISE_ID = uuid4()
EXERCISE_ID = uuid4()


class DummyColumn:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return ("eq", self.name, other)

    def __le__(self, other):
        return ("le", self.name, other)

    def __ge__(self, other):
        return ("ge", self.name, other)

    def desc(self):
        return ("desc", self.name)


class DummyFilterModel:
    user_id = DummyColumn("user_id")
    created_at = DummyColumn("created_at")
    exercise_type = DummyColumn("exercise_type")


class DummyRepository:
    def __init__(self, response=None, model=None):
        self.response = response if response is not None else []
        self.model = model or DummyFilterModel
        self.last_filters = None

    async def get_all(self):
        return self.response

    async def get_filtered(self, *filters):
        self.last_filters = filters
        return self.response


class DummySessionResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class DummySession:
    def __init__(self):
        self.rows = []
        self.last_query = None

    async def execute(self, query):
        self.last_query = query
        return DummySessionResult(self.rows)


class DummyDb:
    def __init__(self):
        self.users = DummyRepository()
        self.diary = DummyRepository(model=DummyFilterModel)
        self.mood_tracker = DummyRepository(model=DummyFilterModel)
        self.exercise = DummyRepository(model=DummyFilterModel)
        self.session = DummySession()


def make_user(user_id=USER_ID, username="user", email="user@example.com", role_id=1):
    return SimpleNamespace(
        id=user_id,
        email=email,
        username=username,
        birth_date=datetime(2000, 1, 1).date(),
        gender="male",
        city="Tomsk",
        phone_number="+70000000000",
        company="Company",
        department="IT",
        job_title="Engineer",
        role_id=role_id,
    )


def make_row(**values):
    return SimpleNamespace(_mapping=values)


@pytest.fixture
def admin_api_client_factory(api_client_factory):
    def _factory(fake_db=None, admin_id=ADMIN_ID):
        fake_db = fake_db or DummyDb()

        async def override_get_db():
            yield fake_db

        async def override_verify_admin():
            return admin_id

        async def _client():
            async for async_client, _ in api_client_factory(
                admin_api_module.router,
                dependency_overrides={
                    get_db: override_get_db,
                    verify_admin: override_verify_admin,
                },
            ):
                yield async_client, fake_db

        return _client()

    return _factory


@pytest.mark.asyncio
async def test_get_users_returns_payload(admin_api_client_factory):
    fake_db = DummyDb()
    fake_db.users.response = [make_user()]

    async for client, _ in admin_api_client_factory(fake_db):
        response = await client.get("/admin/users")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(USER_ID)
    assert response.json()[0]["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_get_users_returns_no_data_message(admin_api_client_factory):
    async for client, _ in admin_api_client_factory():
        response = await client.get("/admin/users")

    assert response.status_code == 200
    assert response.json() == {"message": "Пользователи не найдены", "data": []}


@pytest.mark.asyncio
async def test_get_users_returns_csv(admin_api_client_factory):
    fake_db = DummyDb()
    fake_db.users.response = [make_user()]

    async for client, _ in admin_api_client_factory(fake_db):
        response = await client.get("/admin/users?format=csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "users.csv" in response.headers["content-disposition"]
    assert "user@example.com" in response.text


@pytest.mark.asyncio
async def test_get_users_rejects_unknown_format(admin_api_client_factory):
    async for client, _ in admin_api_client_factory():
        response = await client.get("/admin/users?format=xlsx")

    assert response.status_code == 400
    assert response.json()["detail"] == "Неверный формат вывода. Используйте json или csv"


@pytest.mark.asyncio
async def test_get_users_filter_passes_filters(admin_api_client_factory):
    fake_db = DummyDb()
    fake_db.users.response = [make_user()]

    async for client, db in admin_api_client_factory(fake_db):
        response = await client.get("/admin/users/filter?company=Company&department=IT&gender=male")

    assert response.status_code == 200
    assert len(db.users.last_filters) == 3


@pytest.mark.asyncio
async def test_get_users_filter_rejects_invalid_age_range(admin_api_client_factory):
    async for client, _ in admin_api_client_factory():
        response = await client.get("/admin/users/filter?age_from=50&age_to=20")

    assert response.status_code == 400
    assert response.json()["detail"] == "Минимальный возраст не может быть больше максимального"


@pytest.mark.asyncio
async def test_get_diary_returns_payload(admin_api_client_factory):
    fake_db = DummyDb()
    fake_db.diary.response = [
        SimpleNamespace(id=uuid4(), user_id=USER_ID, text="note", created_at=datetime(2026, 6, 1, 12, 0))
    ]

    async for client, _ in admin_api_client_factory(fake_db):
        response = await client.get("/admin/diary")

    assert response.status_code == 200
    assert response.json()[0]["text"] == "note"


@pytest.mark.asyncio
async def test_get_diary_returns_no_data_message(admin_api_client_factory):
    async for client, _ in admin_api_client_factory():
        response = await client.get("/admin/diary")

    assert response.status_code == 200
    assert response.json() == {"message": "Дневники не найдены", "data": []}


@pytest.mark.asyncio
async def test_get_diary_rejects_invalid_day(admin_api_client_factory):
    async for client, _ in admin_api_client_factory():
        response = await client.get("/admin/diary?day=bad-date")

    assert response.status_code == 400
    assert response.json()["detail"] == "Неверный формат даты. Используйте YYYY-MM-DD"


@pytest.mark.asyncio
async def test_get_mood_tracker_returns_payload(admin_api_client_factory):
    fake_db = DummyDb()
    fake_db.mood_tracker.response = [
        SimpleNamespace(id=uuid4(), user_id=USER_ID, score=70, created_at=datetime(2026, 6, 1, 12, 0))
    ]

    async for client, _ in admin_api_client_factory(fake_db):
        response = await client.get("/admin/mood_tracker")

    assert response.status_code == 200
    assert response.json()[0]["score"] == 70


@pytest.mark.asyncio
async def test_get_mood_tracker_returns_no_data_message(admin_api_client_factory):
    async for client, _ in admin_api_client_factory():
        response = await client.get("/admin/mood_tracker")

    assert response.status_code == 200
    assert response.json() == {"message": "Записи трекера настроения не найдены", "data": []}


@pytest.mark.asyncio
async def test_get_exercises_returns_payload(admin_api_client_factory):
    fake_db = DummyDb()
    fake_db.exercise.response = [
        SimpleNamespace(id=uuid4(), user_id=USER_ID, exercise_type="practice", created_at=datetime(2026, 6, 1, 12, 0))
    ]

    async for client, _ in admin_api_client_factory(fake_db):
        response = await client.get("/admin/exercises")

    assert response.status_code == 200
    assert response.json()[0]["exercise_type"] == "practice"


@pytest.mark.asyncio
async def test_get_exercises_returns_no_data_message(admin_api_client_factory):
    async for client, _ in admin_api_client_factory():
        response = await client.get("/admin/exercises")

    assert response.status_code == 200
    assert response.json() == {"message": "Записи упражнений не найдены", "data": []}


@pytest.mark.asyncio
async def test_get_passed_tests_returns_payload(admin_api_client_factory):
    fake_db = DummyDb()
    fake_db.session.rows = [
        make_row(id=TEST_RESULT_ID, user_id=USER_ID, test_id=TEST_ID, date=datetime(2026, 6, 1, 12, 0))
    ]

    async for client, _ in admin_api_client_factory(fake_db):
        response = await client.get("/admin/passed-tests")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(TEST_RESULT_ID)
    assert response.json()[0]["test_id"] == str(TEST_ID)


@pytest.mark.asyncio
async def test_get_passed_tests_supports_filters_and_csv(admin_api_client_factory):
    fake_db = DummyDb()
    fake_db.session.rows = [
        make_row(id=TEST_RESULT_ID, user_id=USER_ID, test_id=TEST_ID, date=datetime(2026, 6, 1, 12, 0))
    ]

    async for client, _ in admin_api_client_factory(fake_db):
        response = await client.get(
            f"/admin/passed-tests?user_id={USER_ID}&date_from=2026-06-01&date_to=2026-06-05&format=csv"
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "passed_tests.csv" in response.headers["content-disposition"]
    assert str(TEST_ID) in response.text


@pytest.mark.asyncio
async def test_get_passed_tests_returns_no_data_message(admin_api_client_factory):
    async for client, _ in admin_api_client_factory():
        response = await client.get("/admin/passed-tests")

    assert response.status_code == 200
    assert response.json() == {"message": "Пройденные тесты не найдены", "data": []}


@pytest.mark.asyncio
async def test_get_passed_tests_rejects_invalid_period(admin_api_client_factory):
    async for client, _ in admin_api_client_factory():
        response = await client.get("/admin/passed-tests?date_from=2026-06-05&date_to=2026-06-01")

    assert response.status_code == 400
    assert response.json()["detail"] == "Дата начала периода не может быть позже даты окончания"


@pytest.mark.asyncio
async def test_get_passed_exercises_returns_payload(admin_api_client_factory):
    fake_db = DummyDb()
    fake_db.session.rows = [
        make_row(
            id=COMPLETED_EXERCISE_ID,
            user_id=USER_ID,
            exercise_structure_id=EXERCISE_ID,
            date=datetime(2026, 6, 1, 12, 0),
        )
    ]

    async for client, _ in admin_api_client_factory(fake_db):
        response = await client.get("/admin/passed-exercises")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(COMPLETED_EXERCISE_ID)
    assert response.json()[0]["exercise_structure_id"] == str(EXERCISE_ID)


@pytest.mark.asyncio
async def test_get_passed_exercises_supports_filters_and_csv(admin_api_client_factory):
    fake_db = DummyDb()
    fake_db.session.rows = [
        make_row(
            id=COMPLETED_EXERCISE_ID,
            user_id=USER_ID,
            exercise_structure_id=EXERCISE_ID,
            date=datetime(2026, 6, 1, 12, 0),
        )
    ]

    async for client, _ in admin_api_client_factory(fake_db):
        response = await client.get(
            f"/admin/passed-exercises?user_id={USER_ID}&date_from=2026-06-01&date_to=2026-06-05&format=csv"
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "passed_exercises.csv" in response.headers["content-disposition"]
    assert str(EXERCISE_ID) in response.text


@pytest.mark.asyncio
async def test_get_passed_exercises_returns_no_data_message(admin_api_client_factory):
    async for client, _ in admin_api_client_factory():
        response = await client.get("/admin/passed-exercises")

    assert response.status_code == 200
    assert response.json() == {"message": "Пройденные упражнения не найдены", "data": []}


@pytest.mark.asyncio
async def test_get_passed_exercises_rejects_invalid_date(admin_api_client_factory):
    async for client, _ in admin_api_client_factory():
        response = await client.get("/admin/passed-exercises?date_from=bad-date")

    assert response.status_code == 400
    assert response.json()["detail"] == "Неверный формат даты. Используйте YYYY-MM-DD"


@pytest.mark.asyncio
async def test_get_user_statistics_returns_payload(admin_api_client_factory, monkeypatch):
    class DummyStatisticsService:
        def __init__(self, db):
            self.db = db

        async def get_user_activity_statistics(self, user_id):
            return {"user_id": str(user_id), "completed_tests": 2}

    monkeypatch.setattr(admin_api_module, "StatisticsService", DummyStatisticsService)

    async for client, _ in admin_api_client_factory():
        response = await client.get(f"/admin/user-statistics/{USER_ID}")

    assert response.status_code == 200
    assert response.json() == {"user_id": str(USER_ID), "completed_tests": 2}


@pytest.mark.asyncio
async def test_get_user_statistics_returns_no_data_message(admin_api_client_factory, monkeypatch):
    class DummyStatisticsService:
        def __init__(self, db):
            self.db = db

        async def get_user_activity_statistics(self, user_id):
            return None

    monkeypatch.setattr(admin_api_module, "StatisticsService", DummyStatisticsService)

    async for client, _ in admin_api_client_factory():
        response = await client.get(f"/admin/user-statistics/{USER_ID}")

    assert response.status_code == 200
    assert response.json() == {"message": "Статистика пользователя не найдена", "data": []}


@pytest.mark.asyncio
async def test_admin_endpoint_returns_500_for_unexpected_error(admin_api_client_factory):
    fake_db = DummyDb()

    async def raise_error():
        raise RuntimeError("boom")

    fake_db.users.get_all = raise_error

    async for client, _ in admin_api_client_factory(fake_db):
        response = await client.get("/admin/users")

    assert response.status_code == 500
    assert response.json()["detail"] == "Ошибка при обработке запроса админки: boom"
