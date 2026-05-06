import pytest

import src.api.education as education_api_module
from autotest.factories.education import (
    MATERIAL_ID,
    THEME_ID,
    USER_ID,
    build_complete_material_payload,
    build_complete_theme_payload,
    build_theme_response,
    build_theme_with_materials_response,
    build_user_progress_response,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id


class DummyEducationSmokeService:
    def __init__(self, db):
        self.db = db

    async def auto_create_education(self):
        return {"status": "OK", "message": "seeded"}

    async def get_all_education_themes(self):
        return [build_theme_response()]

    async def get_education_theme_materials(self, theme_id, user_id):
        return build_theme_with_materials_response()

    async def complete_education_material(self, payload, user_id):
        return None

    async def complete_education_theme(self, payload, user_id):
        return None

    async def get_user_progress(self, user_id):
        return [build_user_progress_response()]


@pytest.fixture
async def client(api_client_factory, monkeypatch):
    monkeypatch.setattr(education_api_module, "EducationService", DummyEducationSmokeService)

    async def override_get_db():
        yield object()

    def override_get_current_user_id():
        return USER_ID

    async for async_client, _ in api_client_factory(
        education_api_module.router,
        dependency_overrides={
            get_db: override_get_db,
            get_current_user_id: override_get_current_user_id,
        },
    ):
        yield async_client


@pytest.mark.asyncio
async def test_education_auto_create_smoke(client):
    response = await client.post("/education/auto-create")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


@pytest.mark.asyncio
async def test_education_themes_list_smoke(client):
    response = await client.get("/education/themes/all")
    assert response.status_code == 200
    assert response.json()[0]["id"] == str(THEME_ID)


@pytest.mark.asyncio
async def test_education_theme_materials_smoke(client):
    response = await client.get(f"/education/themes/{THEME_ID}/materials/list")
    assert response.status_code == 200
    assert response.json()["education_materials"][0]["id"] == str(MATERIAL_ID)


@pytest.mark.asyncio
async def test_education_complete_material_smoke(client):
    response = await client.post("/education/materials/complete", json=build_complete_material_payload())
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_education_complete_theme_smoke(client):
    response = await client.post("/education/themes/complete", json=build_complete_theme_payload())
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_education_progress_smoke(client):
    response = await client.get("/education/progress")
    assert response.status_code == 200
    assert response.json() == [build_user_progress_response()]
