import datetime
from types import SimpleNamespace

import jwt
import pytest
from itsdangerous import BadData

import src.services.auth as auth_service_module
from autotest4.factories.auth import (
    SECOND_USER_ID,
    USER_ID,
    build_test_result,
    make_user,
)
from src.config import settings
from src.exceptions import (
    EmailNotRegisteredException,
    IncorrectPasswordException,
    IncorrectTokenException,
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    PasswordDoNotMatchException,
    UserAlreadyExistsException,
)
from src.services.auth import AuthService


class FakeUsersRepository:
    def __init__(self):
        self.one_or_none_result = None
        self.user_with_password = None
        self.delete_result = {"status": "OK"}
        self.all_users_admin_result = []
        self.add_calls = []
        self.edit_calls = []
        self.delete_calls = []
        self.get_one_or_none_calls = []
        self.get_user_with_password_calls = []
        self.raise_on_add = None

    async def get_one_or_none(self, **filter_by):
        self.get_one_or_none_calls.append(filter_by)
        return self.one_or_none_result

    async def add(self, data):
        if self.raise_on_add:
            raise self.raise_on_add
        self.add_calls.append(data)

    async def get_user_with_hashed_password(self, **filter_by):
        self.get_user_with_password_calls.append(filter_by)
        return self.user_with_password

    async def delete(self, **filter_by):
        self.delete_calls.append(filter_by)
        return self.delete_result

    async def edit(self, data, exclude_unset=True, **filter_by):
        self.edit_calls.append(
            {"data": data, "exclude_unset": exclude_unset, "filter_by": filter_by}
        )

    async def get_all_users_admin(self):
        return self.all_users_admin_result


class FakeOntologyRepository:
    def __init__(self):
        self.filtered_result = []
        self.raise_on_get = None
        self.calls = []

    async def get_filtered(self, **filter_by):
        self.calls.append(filter_by)
        if self.raise_on_get:
            raise self.raise_on_get
        return self.filtered_result


class FakeAuthDb:
    def __init__(self):
        self.users = FakeUsersRepository()
        self.ontology_entry = FakeOntologyRepository()
        self.commit_count = 0
        self.rollback_count = 0

    async def commit(self):
        self.commit_count += 1

    async def rollback(self):
        self.rollback_count += 1


class DummyDailyTaskService:
    calls = []

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.calls = []

    async def add_daily_tasks_for_new_user(self, user_id):
        type(self).calls.append(user_id)


@pytest.fixture
def fake_auth_db():
    return FakeAuthDb()


@pytest.fixture
def auth_service():
    return AuthService()


@pytest.mark.asyncio
async def test_create_tokens_produces_decodable_access_and_refresh_tokens(auth_service):
    access_token, refresh_token = auth_service.create_tokens(
        {"user_id": str(USER_ID), "role_id": 1}
    )

    access_payload = jwt.decode(
        access_token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    refresh_payload = jwt.decode(
        refresh_token,
        settings.JWT_REFRESH_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

    assert access_payload["user_id"] == str(USER_ID)
    assert refresh_payload["role_id"] == 1


def test_hash_and_verify_password_roundtrip(auth_service):
    hashed = auth_service.hash_password("StrongPass123")

    assert hashed != "StrongPass123"
    assert auth_service.verify_password("StrongPass123", hashed) is True


def test_decode_token_returns_payload(auth_service):
    access_token, _ = auth_service.create_tokens({"user_id": str(USER_ID), "role_id": 1})

    payload = auth_service.decode_token(access_token)

    assert payload["user_id"] == str(USER_ID)


def test_decode_token_raises_for_invalid_token(auth_service):
    with pytest.raises(IncorrectTokenException):
        auth_service.decode_token("bad-token")


def test_decode_token_raises_for_expired_token(auth_service):
    expired_token = jwt.encode(
        {
            "user_id": str(USER_ID),
            "role_id": 1,
            "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(IncorrectTokenException):
        auth_service.decode_token(expired_token)


@pytest.mark.asyncio
async def test_oauth_login_returns_tokens_for_existing_user(fake_auth_db):
    fake_auth_db.users.one_or_none_result = make_user()

    access_token, refresh_token = await AuthService(fake_auth_db).oauth_login(
        "user@example.com",
        "tester",
        "male",
    )

    assert access_token
    assert refresh_token
    assert fake_auth_db.users.add_calls == []
    assert fake_auth_db.commit_count == 0


@pytest.mark.asyncio
async def test_oauth_login_creates_user_when_missing(fake_auth_db):
    fake_auth_db.users.one_or_none_result = None

    access_token, refresh_token = await AuthService(fake_auth_db).oauth_login(
        "user@example.com",
        "tester",
        "male",
    )

    assert access_token
    assert refresh_token
    assert len(fake_auth_db.users.add_calls) == 1
    assert fake_auth_db.commit_count == 1


@pytest.mark.asyncio
async def test_register_user_raises_when_passwords_do_not_match(fake_auth_db):
    data = SimpleNamespace(
        email="user@example.com",
        username="tester",
        birth_date=datetime.date(1999, 1, 1),
        gender="male",
        city="Tomsk",
        phone_number="+70000000000",
        password="one",
        confirm_password="two",
        model_dump=lambda exclude=None: {
            "email": "user@example.com",
            "username": "tester",
            "birth_date": datetime.date(1999, 1, 1),
            "gender": "male",
            "city": "Tomsk",
            "phone_number": "+70000000000",
            "password": "one",
            "confirm_password": "two",
        },
    )

    with pytest.raises(PasswordDoNotMatchException):
        await AuthService(fake_auth_db).register_user(data)


@pytest.mark.asyncio
async def test_register_user_adds_user_commits_and_creates_daily_tasks(fake_auth_db, monkeypatch):
    DummyDailyTaskService.reset()
    monkeypatch.setattr(auth_service_module, "DailyTaskService", DummyDailyTaskService)
    service = AuthService(fake_auth_db)
    service.hash_password = lambda password: "hashed-password"
    data = SimpleNamespace(
        email="user@example.com",
        username="tester",
        birth_date=datetime.date(1999, 1, 1),
        gender="male",
        city="Tomsk",
        phone_number="+70000000000",
        password="StrongPass123",
        confirm_password="StrongPass123",
        model_dump=lambda exclude=None: {
            "email": "user@example.com",
            "username": "tester",
            "birth_date": datetime.date(1999, 1, 1),
            "gender": "male",
            "city": "Tomsk",
            "phone_number": "+70000000000",
        },
    )

    access_token, refresh_token = await service.register_user(data)

    assert access_token
    assert refresh_token
    assert len(fake_auth_db.users.add_calls) == 1
    created = fake_auth_db.users.add_calls[0]
    assert created.hashed_password == "hashed-password"
    assert created.role_id == 1
    assert fake_auth_db.commit_count == 1
    assert DummyDailyTaskService.calls == [created.id]


@pytest.mark.asyncio
async def test_register_user_maps_existing_object_to_user_exists(fake_auth_db, monkeypatch):
    DummyDailyTaskService.reset()
    monkeypatch.setattr(auth_service_module, "DailyTaskService", DummyDailyTaskService)
    fake_auth_db.users.raise_on_add = ObjectAlreadyExistsException()
    service = AuthService(fake_auth_db)
    service.hash_password = lambda password: "hashed-password"
    data = SimpleNamespace(
        email="user@example.com",
        username="tester",
        birth_date=datetime.date(1999, 1, 1),
        gender="male",
        city="Tomsk",
        phone_number="+70000000000",
        password="StrongPass123",
        confirm_password="StrongPass123",
        model_dump=lambda exclude=None: {
            "email": "user@example.com",
            "username": "tester",
            "birth_date": datetime.date(1999, 1, 1),
            "gender": "male",
            "city": "Tomsk",
            "phone_number": "+70000000000",
        },
    )

    with pytest.raises(UserAlreadyExistsException):
        await service.register_user(data)


@pytest.mark.asyncio
async def test_login_user_returns_tokens_for_valid_credentials(fake_auth_db):
    fake_auth_db.users.user_with_password = make_user(hashed_password="hashed")
    service = AuthService(fake_auth_db)
    service.verify_password = lambda plain, hashed: plain == "StrongPass123" and hashed == "hashed"

    access_token, refresh_token = await service.login_user(
        SimpleNamespace(email="user@example.com", password="StrongPass123")
    )

    assert access_token
    assert refresh_token


@pytest.mark.asyncio
async def test_login_user_raises_for_unknown_email(fake_auth_db):
    fake_auth_db.users.user_with_password = None

    with pytest.raises(EmailNotRegisteredException):
        await AuthService(fake_auth_db).login_user(
            SimpleNamespace(email="user@example.com", password="StrongPass123")
        )


@pytest.mark.asyncio
async def test_login_user_raises_for_incorrect_password(fake_auth_db):
    fake_auth_db.users.user_with_password = make_user(hashed_password="hashed")
    service = AuthService(fake_auth_db)
    service.verify_password = lambda plain, hashed: False

    with pytest.raises(IncorrectPasswordException):
        await service.login_user(SimpleNamespace(email="user@example.com", password="bad"))


@pytest.mark.asyncio
async def test_refresh_tokens_returns_new_pair(fake_auth_db):
    fake_auth_db.users.one_or_none_result = make_user()
    service = AuthService(fake_auth_db)
    _, refresh_token = service.create_tokens({"user_id": str(USER_ID), "role_id": 1})

    access_token, new_refresh_token = await service.refresh_tokens(refresh_token)

    assert access_token
    assert new_refresh_token


@pytest.mark.asyncio
async def test_refresh_tokens_raises_when_user_missing(fake_auth_db):
    fake_auth_db.users.one_or_none_result = None
    service = AuthService(fake_auth_db)
    _, refresh_token = service.create_tokens({"user_id": str(USER_ID), "role_id": 1})

    with pytest.raises(IncorrectTokenException):
        await service.refresh_tokens(refresh_token)


@pytest.mark.asyncio
async def test_refresh_tokens_raises_for_invalid_token(fake_auth_db):
    with pytest.raises(IncorrectTokenException):
        await AuthService(fake_auth_db).refresh_tokens("bad-refresh-token")


@pytest.mark.asyncio
async def test_refresh_tokens_raises_when_repository_fails(fake_auth_db, monkeypatch):
    service = AuthService(fake_auth_db)
    monkeypatch.setattr(
        service,
        "decode_token",
        lambda token, is_refresh=True: {"user_id": str(USER_ID), "role_id": 1},
    )

    async def raise_lookup(**filter_by):
        raise RuntimeError("lookup failed")

    fake_auth_db.users.get_one_or_none = raise_lookup

    with pytest.raises(IncorrectTokenException):
        await service.refresh_tokens("refresh-token")


@pytest.mark.asyncio
async def test_get_one_or_none_user_delegates_to_repository(fake_auth_db):
    fake_auth_db.users.one_or_none_result = make_user()

    result = await AuthService(fake_auth_db).get_one_or_none_user(id=USER_ID)

    assert result.id == USER_ID
    assert fake_auth_db.users.get_one_or_none_calls == [{"id": USER_ID}]


@pytest.mark.asyncio
async def test_delete_user_delegates_to_repository(fake_auth_db):
    result = await AuthService(fake_auth_db).delete_user(id=USER_ID)

    assert result == {"status": "OK"}
    assert fake_auth_db.users.delete_calls == [{"id": USER_ID}]


@pytest.mark.asyncio
async def test_change_password_updates_hash_and_commits(fake_auth_db, monkeypatch):
    monkeypatch.setattr(auth_service_module.serializer, "loads", lambda token, max_age=3600: "user@example.com")
    service = AuthService(fake_auth_db)
    service.hash_password = lambda password: "hashed-password"

    await service.change_password(
        SimpleNamespace(
            token="reset-token",
            password="NewStrongPass123",
            confirm_new_password="NewStrongPass123",
        )
    )

    assert fake_auth_db.users.edit_calls[0]["filter_by"] == {"email": "user@example.com"}
    assert fake_auth_db.users.edit_calls[0]["data"].hashed_password == "hashed-password"
    assert fake_auth_db.commit_count == 1


@pytest.mark.asyncio
async def test_change_password_raises_for_bad_token(fake_auth_db, monkeypatch):
    def raise_bad_data(token, max_age=3600):
        raise BadData("bad")

    monkeypatch.setattr(auth_service_module.serializer, "loads", raise_bad_data)

    with pytest.raises(IncorrectTokenException):
        await AuthService(fake_auth_db).change_password(
            SimpleNamespace(
                token="bad-token",
                password="NewStrongPass123",
                confirm_new_password="NewStrongPass123",
            )
        )


@pytest.mark.asyncio
async def test_change_password_raises_for_mismatch(fake_auth_db, monkeypatch):
    monkeypatch.setattr(auth_service_module.serializer, "loads", lambda token, max_age=3600: "user@example.com")

    with pytest.raises(PasswordDoNotMatchException):
        await AuthService(fake_auth_db).change_password(
            SimpleNamespace(
                token="reset-token",
                password="one",
                confirm_new_password="two",
            )
        )


@pytest.mark.asyncio
async def test_change_password_propagates_repository_edit(fake_auth_db, monkeypatch):
    monkeypatch.setattr(auth_service_module.serializer, "loads", lambda token, max_age=3600: "user@example.com")
    fake_auth_db.users.edit_calls = []
    service = AuthService(fake_auth_db)
    service.hash_password = lambda password: "hashed-password"

    await service.change_password(
        SimpleNamespace(
            token="reset-token",
            password="one",
            confirm_new_password="one",
        )
    )

    assert fake_auth_db.users.edit_calls[0]["exclude_unset"] is True


@pytest.mark.asyncio
async def test_update_user_edits_and_commits(fake_auth_db):
    fake_auth_db.users.one_or_none_result = make_user()

    await AuthService(fake_auth_db).update_user(
        USER_ID,
        SimpleNamespace(username="updated"),
    )

    assert fake_auth_db.users.edit_calls[0]["filter_by"] == {"id": USER_ID}
    assert fake_auth_db.commit_count == 1


@pytest.mark.asyncio
async def test_update_user_raises_when_user_missing(fake_auth_db):
    fake_auth_db.users.one_or_none_result = None

    with pytest.raises(ObjectNotFoundException):
        await AuthService(fake_auth_db).update_user(
            USER_ID,
            SimpleNamespace(username="updated"),
        )


@pytest.mark.asyncio
async def test_get_all_users_admin_delegates_to_repository(fake_auth_db):
    fake_auth_db.users.all_users_admin_result = [make_user(), make_user(user_id=SECOND_USER_ID)]

    result = await AuthService(fake_auth_db).get_all_users_admin()

    assert len(result) == 2


@pytest.mark.asyncio
async def test_register_admin_rolls_back_on_internal_error(fake_auth_db):
    fake_auth_db.users.one_or_none_result = None

    with pytest.raises(TypeError):
        await AuthService(fake_auth_db).register_admin(
            email="admin@example.com",
            password="StrongPass123",
            username="admin",
        )

    assert fake_auth_db.rollback_count == 1


@pytest.mark.asyncio
async def test_register_admin_raises_when_user_already_exists(fake_auth_db):
    fake_auth_db.users.one_or_none_result = make_user(email="admin@example.com")

    with pytest.raises(Exception):
        await AuthService(fake_auth_db).register_admin(
            email="admin@example.com",
            password="StrongPass123",
            username="admin",
        )

    assert fake_auth_db.rollback_count == 1


@pytest.mark.asyncio
async def test_burnout_calculate_raises_for_empty_results(fake_auth_db):
    with pytest.raises(ValueError):
        await AuthService(fake_auth_db).burnout_calculate([])


@pytest.mark.asyncio
async def test_burnout_calculate_raises_when_scale_results_missing(fake_auth_db):
    with pytest.raises(ValueError):
        await AuthService(fake_auth_db).burnout_calculate([{"datetime": "2026-04-10T10:00:00"}])


@pytest.mark.asyncio
async def test_burnout_calculate_uses_latest_test_and_score_order(fake_auth_db, monkeypatch):
    captured = {}

    def fake_burnout_calculate(*scores):
        captured["scores"] = scores
        return 0.73

    monkeypatch.setattr(auth_service_module, "burnout_calculate", fake_burnout_calculate)
    result = await AuthService(fake_auth_db).burnout_calculate(
        [
            build_test_result("2026-04-10T09:00:00", [1, 1, 1, 1, 1]),
            build_test_result("2026-04-10T10:00:00", [2, 3, 4, 5, 6]),
        ]
    )

    assert result == 0.73
    assert captured["scores"] == (2, 3, 4, 5, 6)


@pytest.mark.asyncio
async def test_get_ontology_returns_repository_result(fake_auth_db):
    fake_auth_db.ontology_entry.filtered_result = ["item-1"]

    result = await AuthService(fake_auth_db).get_ontology(USER_ID)

    assert result == ["item-1"]
    assert fake_auth_db.ontology_entry.calls == [{"user_id": USER_ID}]


@pytest.mark.asyncio
async def test_get_ontology_rolls_back_and_reraises(fake_auth_db):
    fake_auth_db.ontology_entry.raise_on_get = RuntimeError("db failed")

    with pytest.raises(RuntimeError):
        await AuthService(fake_auth_db).get_ontology(USER_ID)

    assert fake_auth_db.rollback_count == 1
