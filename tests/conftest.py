# ruff: noqa: E402
import pytest
import json

from unittest import mock

mock.patch("fastapi_cache.decorator.cache", lambda *args, **kwargs: lambda f: f).start()

from src.config import settings
from src.database import Base, engine_null_pool, async_session_maker_null_pool
from src.main import app
from src.api.dependencies.db import get_db
from httpx import AsyncClient, ASGITransport
from src.models import *  # noqa

from src.utils.db_manager import DBManager


@pytest.fixture(scope="session", autouse=True)
def check_test_mode():
    assert settings.MODE == "TEST"


@pytest.fixture(scope="session", autouse=True)
async def setup_database(check_test_mode):
    async with engine_null_pool.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def get_db_null_pool():
    async with DBManager(session_factory=async_session_maker_null_pool) as db:
        yield db


@pytest.fixture(scope="function")
async def db() -> DBManager:
    async for db in get_db_null_pool():
        yield db


app.dependency_overrides[get_db] = get_db_null_pool


@pytest.fixture(scope="session")
async def ac() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture(scope="session", autouse=True)
async def register_user(ac, setup_database):
    data = {
        "email": "user@example.com",
        "username": "string",
        "birth_date": "2025-02-22",
        "gender": "string",
        "city": "string",
        "phone_number": "string",
        "password": "string",
        "confirm_password": "string",
    }
    await ac.post("/auth/register", json=data)


@pytest.fixture(scope="session")
async def authenticated_ac(ac, register_user):
    await ac.post(
        "/auth/login", json={"email": "maksimka@yandex.ru", "password": "1234"}
    )
    assert ac.cookies["access_token"]
    yield ac
