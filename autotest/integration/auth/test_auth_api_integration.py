from sqlalchemy import select

import pytest

import src.api.auth as auth_api_module
import src.services.auth as auth_service_module
from autotest4.factories.auth import (
    USER_ID,
    build_login_payload,
    build_password_change_payload,
    build_password_reset_request,
    build_refresh_payload,
    build_register_payload,
    build_update_user_payload,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.models.users import UsersOrm
from src.services.auth import AuthService

def header_values(response, name):
    getter = getattr(response.headers, "get_list", None)
    if getter is not None:
        return getter(name)
    return response.headers.getlist(name)


def build_user_orm(*, user_id=USER_ID, email="user@example.com", hashed_password="hashed", username="tester"):
    return UsersOrm(
        id=user_id,
        email=email,
        username=username,
        hashed_password=hashed_password,
        city="Tomsk",
        company=None,
        online=None,
        gender="male",
        birth_date=__import__("datetime").date(1999, 1, 1),
        phone_number="+70000000000",
        description=None,
        role_id=1,
        is_active=True,
        department=None,
        job_title=None,
        face_to_face=None,
    )


class DummyDailyTaskService:
    calls = []

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.calls = []

    async def add_daily_tasks_for_new_user(self, user_id):
        type(self).calls.append(user_id)


class DummyDelay:
    calls = []

    @classmethod
    def reset(cls):
        cls.calls = []

    @classmethod
    def delay(cls, email):
        cls.calls.append(email)


@pytest.fixture
def auth_integration_client_factory(api_client_factory, integration_db_manager_factory, monkeypatch):
    DummyDailyTaskService.reset()
    DummyDelay.reset()
    monkeypatch.setattr(auth_service_module, "DailyTaskService", DummyDailyTaskService)
    monkeypatch.setattr(auth_api_module.send_email_to_recover_password, "delay", DummyDelay.delay)

    def _factory(user_id=USER_ID):
        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                auth_api_module.router,
                dependency_overrides={
                    get_db: integration_db_manager_factory,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client

        return _client()

    return _factory


async def fetch_user(session_factory, email="user@example.com"):
    async with session_factory() as session:
        result = await session.execute(select(UsersOrm).filter_by(email=email))
        return result.scalars().one_or_none()


@pytest.mark.asyncio
async def test_register_integration_persists_user_and_returns_tokens(
    auth_integration_client_factory,
    integration_session_factory,
):
    async for client in auth_integration_client_factory():
        response = await client.post("/auth/register", json=build_register_payload())

    assert response.status_code == 200
    body = response.json()
    assert {"access_token", "refresh_token"} == set(body.keys())
    created_user = await fetch_user(integration_session_factory)
    assert created_user is not None
    assert created_user.username == "tester"
    assert created_user.hashed_password != "StrongPass123"
    assert DummyDailyTaskService.calls == [created_user.id]


@pytest.mark.asyncio
async def test_login_integration_checks_real_hash_and_sets_cookies(
    auth_integration_client_factory,
    integration_session_factory,
):
    service = AuthService()
    hashed_password = service.hash_password("StrongPass123")
    async with integration_session_factory() as session:
        session.add(build_user_orm(hashed_password=hashed_password))
        await session.commit()

    async for client in auth_integration_client_factory():
        response = await client.post("/auth/login", json=build_login_payload())

    assert response.status_code == 200
    cookie_header = header_values(response, "set-cookie")
    assert any("access_token=" in item for item in cookie_header)
    assert any("refresh_token=" in item for item in cookie_header)


@pytest.mark.asyncio
async def test_token_auth_integration_returns_new_pair_for_valid_access_token(
    auth_integration_client_factory,
    integration_session_factory,
    monkeypatch,
):
    async with integration_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    monkeypatch.setattr(AuthService, "decode_token", lambda self, token: {"user_id": USER_ID, "role_id": 1})

    async for client in auth_integration_client_factory():
        response = await client.post("/auth/token-auth?token=access-token")

    assert response.status_code == 200
    assert {"access_token", "refresh_token"} == set(response.json().keys())


@pytest.mark.asyncio
async def test_refresh_token_integration_returns_new_pair_for_valid_refresh_token(
    auth_integration_client_factory,
    integration_session_factory,
    monkeypatch,
):
    async with integration_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    monkeypatch.setattr(
        AuthService,
        "decode_token",
        lambda self, token, is_refresh=True: {"user_id": str(USER_ID), "role_id": 1},
    )

    async for client in auth_integration_client_factory():
        response = await client.post("/auth/refresh-token", json=build_refresh_payload("refresh-token"))

    assert response.status_code == 200
    body = response.json()
    assert {"access_token", "refresh_token"} == set(body.keys())


@pytest.mark.asyncio
async def test_me_update_and_delete_integration_use_real_database(
    auth_integration_client_factory,
    integration_session_factory,
):
    async with integration_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    async for client in auth_integration_client_factory():
        me_response = await client.get("/auth/me")
        update_response = await client.patch("/auth/update", json=build_update_user_payload(username="real-update"))
        delete_response = await client.delete("/auth/delete")

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "user@example.com"
    assert update_response.status_code == 200
    assert delete_response.status_code == 200
    deleted_user = await fetch_user(integration_session_factory)
    assert deleted_user is None


@pytest.mark.asyncio
async def test_logout_integration_clears_cookies(auth_integration_client_factory):
    async for client in auth_integration_client_factory():
        response = await client.post("/auth/logout")

    assert response.status_code == 200
    cookie_header = header_values(response, "set-cookie")
    assert any("access_token=" in item and "Max-Age=0" in item for item in cookie_header)
    assert any("refresh_token=" in item and "Max-Age=0" in item for item in cookie_header)


@pytest.mark.asyncio
async def test_password_reset_request_integration_enqueues_email_when_user_exists(
    auth_integration_client_factory,
    integration_session_factory,
):
    async with integration_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    async for client in auth_integration_client_factory():
        response = await client.post(
            "/auth/request-password-reset",
            json=build_password_reset_request(),
        )

    assert response.status_code == 200
    assert DummyDelay.calls == ["user@example.com"]


@pytest.mark.asyncio
async def test_password_reset_request_integration_returns_404_when_user_missing(
    auth_integration_client_factory,
):
    async for client in auth_integration_client_factory():
        response = await client.post(
            "/auth/request-password-reset",
            json=build_password_reset_request(),
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_password_change_integration_updates_persisted_hash(
    auth_integration_client_factory,
    integration_session_factory,
    monkeypatch,
):
    async with integration_session_factory() as session:
        session.add(build_user_orm(hashed_password="old-hash"))
        await session.commit()

    monkeypatch.setattr(auth_service_module.serializer, "loads", lambda token, max_age=3600: "user@example.com")

    async for client in auth_integration_client_factory():
        response = await client.post("/auth/password-reset", json=build_password_change_payload())

    assert response.status_code == 200
    updated_user = await fetch_user(integration_session_factory)
    assert updated_user.hashed_password != "old-hash"
    assert AuthService().verify_password("NewStrongPass123", updated_user.hashed_password) is True
