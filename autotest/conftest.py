import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.api.chat_bot import router as chat_bot_router


@pytest.fixture
async def client():
    app = FastAPI()
    app.include_router(chat_bot_router)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


@pytest.fixture
def app_factory():
    def _create_app(*routers):
        app = FastAPI()
        for router in routers:
            app.include_router(router)
        return app

    return _create_app


@pytest.fixture
def api_client_factory(app_factory):
    def _create_client(router, *, dependency_overrides=None, raise_app_exceptions=False):
        app = app_factory(router)
        for dependency, override in (dependency_overrides or {}).items():
            app.dependency_overrides[dependency] = override

        async def _client():
            async with AsyncClient(
                transport=ASGITransport(app=app, raise_app_exceptions=raise_app_exceptions),
                base_url="http://testserver",
            ) as async_client:
                yield async_client, app

        return _client()

    return _create_client
