import pytest

import src.api.auth as auth_api_module
from autotest4.factories.auth import (
    USER_ID,
    build_login_payload,
    build_refresh_payload,
    build_register_payload,
    make_user,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id


class DummyAuthSmokeService:
    def __init__(self, db):
        self.db = db

    async def get_one_or_none_user(self, **filter_by):
        return make_user()

    async def register_user(self, data):
        return ("access-token", "refresh-token")

    async def login_user(self, data):
        return ("access-token", "refresh-token")

    async def refresh_tokens(self, refresh_token):
        return ("new-access-token", "new-refresh-token")


@pytest.fixture
async def client(api_client_factory, monkeypatch):
    monkeypatch.setattr(auth_api_module, "AuthService", DummyAuthSmokeService)

    async def override_get_db():
        yield object()

    def override_get_current_user_id():
        return USER_ID

    async for async_client, _ in api_client_factory(
        auth_api_module.router,
        dependency_overrides={
            get_db: override_get_db,
            get_current_user_id: override_get_current_user_id,
        },
    ):
        yield async_client


@pytest.mark.asyncio
async def test_auth_me_smoke(client):
    response = await client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(USER_ID)


@pytest.mark.asyncio
async def test_auth_register_smoke(client):
    response = await client.post("/auth/register", json=build_register_payload())

    assert response.status_code == 200
    assert response.json() == {"access_token": "access-token", "refresh_token": "refresh-token"}


@pytest.mark.asyncio
async def test_auth_login_smoke(client):
    response = await client.post("/auth/login", json=build_login_payload())

    assert response.status_code == 200
    assert response.json() == {"access_token": "access-token", "refresh_token": "refresh-token"}


@pytest.mark.asyncio
async def test_auth_refresh_smoke(client):
    response = await client.post("/auth/refresh-token", json=build_refresh_payload())

    assert response.status_code == 200
    assert response.json() == {"access_token": "new-access-token", "refresh_token": "new-refresh-token"}
