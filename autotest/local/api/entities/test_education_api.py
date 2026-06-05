import pytest

import src.api.education as education_api_module
from autotest.factories.education import (
    CARD_ID,
    MATERIAL_ID,
    THEME_ID,
    USER_ID,
    build_card_create_payload,
    build_complete_material_payload,
    build_complete_theme_payload,
    build_material_create_payload,
    build_theme_create_payload,
    build_card_response,
    build_material_response,
    build_theme_response,
    build_theme_with_materials_response,
    build_user_progress_response,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.exceptions import ObjectAlreadyExistsException, ObjectNotFoundException


class DummyEducationApiService:
    auto_create_response = {"status": "OK", "message": "seeded"}
    themes_response = [build_theme_response()]
    theme_materials_response = build_theme_with_materials_response()
    progress_response = [build_user_progress_response()]
    raise_on_auto_create = None
    raise_on_get_themes = None
    raise_on_get_theme_materials = None
    raise_on_complete_material = None
    raise_on_complete_theme = None
    raise_on_get_progress = None
    last_init_db = None
    last_theme_materials_args = None
    last_complete_material_args = None
    last_complete_theme_args = None
    last_progress_user_id = None
    last_create_theme_payload = None
    last_update_theme_args = None
    last_delete_theme_id = None
    last_create_material_args = None
    last_update_material_args = None
    last_delete_material_id = None
    last_create_card_args = None
    last_update_card_args = None
    last_delete_card_id = None

    def __init__(self, db):
        self.db = db
        type(self).last_init_db = db

    @classmethod
    def reset(cls):
        cls.auto_create_response = {"status": "OK", "message": "seeded"}
        cls.themes_response = [build_theme_response()]
        cls.theme_materials_response = build_theme_with_materials_response()
        cls.progress_response = [build_user_progress_response()]
        cls.raise_on_auto_create = None
        cls.raise_on_get_themes = None
        cls.raise_on_get_theme_materials = None
        cls.raise_on_complete_material = None
        cls.raise_on_complete_theme = None
        cls.raise_on_get_progress = None
        cls.last_init_db = None
        cls.last_theme_materials_args = None
        cls.last_complete_material_args = None
        cls.last_complete_theme_args = None
        cls.last_progress_user_id = None
        cls.last_create_theme_payload = None
        cls.last_update_theme_args = None
        cls.last_delete_theme_id = None
        cls.last_create_material_args = None
        cls.last_update_material_args = None
        cls.last_delete_material_id = None
        cls.last_create_card_args = None
        cls.last_update_card_args = None
        cls.last_delete_card_id = None

    async def auto_create_education(self):
        if type(self).raise_on_auto_create:
            raise type(self).raise_on_auto_create
        return type(self).auto_create_response

    async def create_theme(self, theme_data):
        type(self).last_create_theme_payload = theme_data
        return build_theme_response()

    async def update_theme(self, theme_id, theme_data):
        type(self).last_update_theme_args = (theme_id, theme_data)
        return build_theme_response()

    async def delete_theme(self, theme_id):
        type(self).last_delete_theme_id = theme_id

    async def create_material(self, theme_id, material_data):
        type(self).last_create_material_args = (theme_id, material_data)
        return build_material_response()

    async def update_material(self, material_id, material_data):
        type(self).last_update_material_args = (material_id, material_data)
        return build_material_response()

    async def delete_material(self, material_id):
        type(self).last_delete_material_id = material_id

    async def create_card(self, material_id, card_data):
        type(self).last_create_card_args = (material_id, card_data)
        return build_card_response()

    async def update_card(self, card_id, card_data):
        type(self).last_update_card_args = (card_id, card_data)
        return build_card_response()

    async def delete_card(self, card_id):
        type(self).last_delete_card_id = card_id

    async def get_all_education_themes(self):
        if type(self).raise_on_get_themes:
            raise type(self).raise_on_get_themes
        return type(self).themes_response

    async def get_education_theme_materials(self, theme_id, user_id):
        if type(self).raise_on_get_theme_materials:
            raise type(self).raise_on_get_theme_materials
        type(self).last_theme_materials_args = (theme_id, user_id)
        return type(self).theme_materials_response

    async def complete_education_material(self, payload, user_id):
        if type(self).raise_on_complete_material:
            raise type(self).raise_on_complete_material
        type(self).last_complete_material_args = (payload, user_id)

    async def complete_education_theme(self, payload, user_id):
        if type(self).raise_on_complete_theme:
            raise type(self).raise_on_complete_theme
        type(self).last_complete_theme_args = (payload, user_id)

    async def get_user_progress(self, user_id):
        if type(self).raise_on_get_progress:
            raise type(self).raise_on_get_progress
        type(self).last_progress_user_id = user_id
        return type(self).progress_response


@pytest.fixture
def education_api_client_factory(api_client_factory, monkeypatch):
    DummyEducationApiService.reset()
    monkeypatch.setattr(education_api_module, "EducationService", DummyEducationApiService)

    def _factory(user_id=USER_ID):
        fake_db = object()

        async def override_get_db():
            yield fake_db

        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                education_api_module.router,
                dependency_overrides={
                    get_db: override_get_db,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client, fake_db

        return _client()

    return _factory


@pytest.mark.asyncio
async def test_auto_create_education_returns_service_payload(education_api_client_factory):
    async for client, fake_db in education_api_client_factory():
        response = await client.post("/education/auto-create")

    assert response.status_code == 200
    assert response.json() == {"status": "OK", "message": "seeded"}
    assert DummyEducationApiService.last_init_db is fake_db


@pytest.mark.asyncio
async def test_auto_create_education_returns_500_on_unexpected_error(education_api_client_factory):
    DummyEducationApiService.raise_on_auto_create = RuntimeError("boom")

    async for client, _ in education_api_client_factory():
        response = await client.post("/education/auto-create")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_education_crud_endpoints_delegate_payloads(education_api_client_factory):
    async for client, _ in education_api_client_factory():
        create_theme_response = await client.post("/education/themes", json=build_theme_create_payload())
        update_theme_response = await client.patch(f"/education/themes/{THEME_ID}", json={"theme": "Updated"})
        delete_theme_response = await client.delete(f"/education/themes/{THEME_ID}")
        create_material_response = await client.post(
            f"/education/themes/{THEME_ID}/materials",
            json=build_material_create_payload(),
        )
        update_material_response = await client.patch(
            f"/education/materials/{MATERIAL_ID}",
            json={"title": "Updated material"},
        )
        delete_material_response = await client.delete(f"/education/materials/{MATERIAL_ID}")
        create_card_response = await client.post(
            f"/education/materials/{MATERIAL_ID}/cards",
            json=build_card_create_payload(),
        )
        update_card_response = await client.patch(
            f"/education/cards/{CARD_ID}",
            json={"text": "Updated card"},
        )
        delete_card_response = await client.delete(f"/education/cards/{CARD_ID}")

    assert create_theme_response.status_code == 200
    assert update_theme_response.status_code == 200
    assert delete_theme_response.status_code == 204
    assert create_material_response.status_code == 200
    assert update_material_response.status_code == 200
    assert delete_material_response.status_code == 204
    assert create_card_response.status_code == 200
    assert update_card_response.status_code == 200
    assert delete_card_response.status_code == 204
    assert DummyEducationApiService.last_create_theme_payload.theme == "Theme title"
    assert DummyEducationApiService.last_update_theme_args[0] == THEME_ID
    assert DummyEducationApiService.last_delete_theme_id == THEME_ID
    assert DummyEducationApiService.last_create_material_args[0] == THEME_ID
    assert DummyEducationApiService.last_update_material_args[0] == MATERIAL_ID
    assert DummyEducationApiService.last_delete_material_id == MATERIAL_ID
    assert DummyEducationApiService.last_create_card_args[0] == MATERIAL_ID
    assert DummyEducationApiService.last_update_card_args[0] == CARD_ID
    assert DummyEducationApiService.last_delete_card_id == CARD_ID


@pytest.mark.asyncio
async def test_get_all_education_themes_returns_nested_payload(education_api_client_factory):
    async for client, _ in education_api_client_factory():
        response = await client.get("/education/themes/all")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(THEME_ID)
    assert response.json()[0]["education_materials"][0]["id"] == str(MATERIAL_ID)


@pytest.mark.asyncio
async def test_get_all_education_themes_returns_empty_list(education_api_client_factory):
    DummyEducationApiService.themes_response = []

    async for client, _ in education_api_client_factory():
        response = await client.get("/education/themes/all")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_all_education_themes_returns_500_on_unexpected_error(education_api_client_factory):
    DummyEducationApiService.raise_on_get_themes = RuntimeError("boom")

    async for client, _ in education_api_client_factory():
        response = await client.get("/education/themes/all")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_education_theme_materials_returns_materials_and_recommendations(education_api_client_factory):
    async for client, _ in education_api_client_factory():
        response = await client.get(f"/education/themes/{THEME_ID}/materials/list")

    assert response.status_code == 200
    assert response.json()["id"] == str(THEME_ID)
    assert len(response.json()["recommendations"]) == 1
    assert len(response.json()["education_materials"][0]["cards"]) == 1
    assert DummyEducationApiService.last_theme_materials_args == (THEME_ID, USER_ID)


@pytest.mark.asyncio
async def test_get_education_theme_materials_returns_404_when_service_reports_missing_object(
    education_api_client_factory,
):
    DummyEducationApiService.raise_on_get_theme_materials = ObjectNotFoundException()

    async for client, _ in education_api_client_factory():
        response = await client.get(f"/education/themes/{THEME_ID}/materials/list")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_education_theme_materials_returns_422_for_invalid_uuid(education_api_client_factory):
    async for client, _ in education_api_client_factory():
        response = await client.get("/education/themes/not-a-uuid/materials/list")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_education_theme_materials_returns_500_on_unexpected_error(education_api_client_factory):
    DummyEducationApiService.raise_on_get_theme_materials = RuntimeError("boom")

    async for client, _ in education_api_client_factory():
        response = await client.get(f"/education/themes/{THEME_ID}/materials/list")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_complete_education_material_returns_ok(education_api_client_factory):
    async for client, _ in education_api_client_factory():
        response = await client.post("/education/materials/complete", json=build_complete_material_payload())

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    payload, user_id = DummyEducationApiService.last_complete_material_args
    assert payload.education_material_id == MATERIAL_ID
    assert user_id == USER_ID


@pytest.mark.asyncio
async def test_complete_education_material_returns_404_when_material_missing(education_api_client_factory):
    DummyEducationApiService.raise_on_complete_material = ObjectNotFoundException()

    async for client, _ in education_api_client_factory():
        response = await client.post("/education/materials/complete", json=build_complete_material_payload())

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_complete_education_material_returns_409_for_duplicate_completion(education_api_client_factory):
    DummyEducationApiService.raise_on_complete_material = ObjectAlreadyExistsException()

    async for client, _ in education_api_client_factory():
        response = await client.post("/education/materials/complete", json=build_complete_material_payload())

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_complete_education_material_returns_422_for_invalid_payload(education_api_client_factory):
    async for client, _ in education_api_client_factory():
        response = await client.post("/education/materials/complete", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_complete_education_material_returns_500_on_unexpected_error(education_api_client_factory):
    DummyEducationApiService.raise_on_complete_material = RuntimeError("boom")

    async for client, _ in education_api_client_factory():
        response = await client.post("/education/materials/complete", json=build_complete_material_payload())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_complete_education_theme_returns_ok(education_api_client_factory):
    async for client, _ in education_api_client_factory():
        response = await client.post("/education/themes/complete", json=build_complete_theme_payload())

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    payload, user_id = DummyEducationApiService.last_complete_theme_args
    assert payload.education_theme_id == THEME_ID
    assert user_id == USER_ID


@pytest.mark.asyncio
async def test_complete_education_theme_returns_404_when_theme_missing(education_api_client_factory):
    DummyEducationApiService.raise_on_complete_theme = ObjectNotFoundException()

    async for client, _ in education_api_client_factory():
        response = await client.post("/education/themes/complete", json=build_complete_theme_payload())

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_complete_education_theme_returns_409_when_already_completed(education_api_client_factory):
    DummyEducationApiService.raise_on_complete_theme = ObjectAlreadyExistsException()

    async for client, _ in education_api_client_factory():
        response = await client.post("/education/themes/complete", json=build_complete_theme_payload())

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_complete_education_theme_returns_422_for_invalid_payload(education_api_client_factory):
    async for client, _ in education_api_client_factory():
        response = await client.post("/education/themes/complete", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_complete_education_theme_returns_500_on_unexpected_error(education_api_client_factory):
    DummyEducationApiService.raise_on_complete_theme = RuntimeError("boom")

    async for client, _ in education_api_client_factory():
        response = await client.post("/education/themes/complete", json=build_complete_theme_payload())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_user_progress_returns_payload(education_api_client_factory):
    async for client, _ in education_api_client_factory():
        response = await client.get("/education/progress")

    assert response.status_code == 200
    assert response.json() == [build_user_progress_response()]
    assert DummyEducationApiService.last_progress_user_id == USER_ID


@pytest.mark.asyncio
async def test_get_user_progress_returns_empty_list(education_api_client_factory):
    DummyEducationApiService.progress_response = []

    async for client, _ in education_api_client_factory():
        response = await client.get("/education/progress")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_user_progress_returns_500_on_unexpected_error(education_api_client_factory):
    DummyEducationApiService.raise_on_get_progress = RuntimeError("boom")

    async for client, _ in education_api_client_factory():
        response = await client.get("/education/progress")

    assert response.status_code == 500
