import json
import uuid
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, update
from sqlalchemy.orm import Session

from src.api.dependencies.db import get_db
from src.api.mood_tracker import router
from src.models.education import educationThemeOrm
from src.models.exercise import ExerciseStructureOrm
from src.models.tests import TestOrm as QuestionnaireOrm
from src.repositories.education_theme import EducationThemeRepository
from src.repositories.exercise import ExerciseRepository
from src.repositories.tests import TestsRepository as QuestionnaireRepository
from src.services.fixtures.education import EDUCATION
from src.services.fixtures.exercise import EXERCISES
from src.services.mood_tracker import MOOD_HELP_MATERIALS


@pytest.fixture
def help_db():
    engine = create_engine("sqlite:///:memory:")
    for model in (QuestionnaireOrm, ExerciseStructureOrm, educationThemeOrm):
        model.__table__.create(engine)
    session = Session(engine, expire_on_commit=False)
    tests = {
        item["id"]: item
        for item in json.loads(
            Path("src/services/info/test_info.json").read_text(encoding="utf-8")
        )
    }
    exercises = {item["id"]: item for item in EXERCISES}
    themes = {item["id"]: item for item in EDUCATION}
    for references in MOOD_HELP_MATERIALS.values():
        for reference in references:
            material_id = uuid.UUID(reference.material_id)
            if reference.type == "test":
                item = tests[reference.material_id]
                session.add(
                    QuestionnaireOrm(
                        id=material_id,
                        title=item["title"],
                        description=item["description"],
                        short_desc=item["short_desc"],
                        link=item["link"],
                        type=0,
                    )
                )
            elif reference.type == "practice":
                item = exercises[reference.material_id]
                session.add(
                    ExerciseStructureOrm(
                        id=material_id,
                        title=item["title"],
                        description=item["description"],
                        picture_link=item["picture_link"],
                        time_to_read=item["time_to_read"],
                        questions_count=item["questions_count"],
                        sort_order=item["sort_order"],
                        group=item["group"],
                    )
                )
            else:
                item = themes[reference.material_id]
                session.add(
                    educationThemeOrm(
                        id=material_id,
                        theme=item["theme"],
                        link=item["link"],
                        link_to_picture=item["link_to_picture"],
                    )
                )
    session.commit()

    async def execute(statement):
        return session.execute(statement)

    adapter = SimpleNamespace(execute=execute)
    db = SimpleNamespace(
        tests=QuestionnaireRepository(adapter),
        exercise=ExerciseRepository(adapter),
        education_theme=EducationThemeRepository(adapter),
    )
    try:
        yield db, session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
async def help_client(help_db):
    db, _ = help_db
    app = FastAPI()
    app.include_router(router)

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://api.example.com"
    ) as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.parametrize("category", ["reflect", "relax", "focus"])
async def test_help_cards_include_titles_images_and_existing_references(
    help_client, category
):
    response = await help_client.get(f"/mood_tracker/help-categories/{category}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == category
    assert body["title"]
    assert [(item["type"], item["material_id"]) for item in body["materials"]] == [
        (reference.type, reference.material_id)
        for reference in MOOD_HELP_MATERIALS[category]
    ]
    for material in body["materials"]:
        assert set(material) == {"type", "material_id", "title", "image_url"}
        assert material["title"]
        assert material["image_url"].startswith("/images/")
        assert (
            Path("src") / urlparse(material["image_url"]).path.lstrip("/")
        ).is_file()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category,model,title_field,image_field",
    [
        ("reflect", QuestionnaireOrm, "title", "link"),
        ("relax", educationThemeOrm, "theme", "link_to_picture"),
        ("focus", ExerciseStructureOrm, "title", "picture_link"),
    ],
)
async def test_help_cards_read_current_metadata_from_database(
    help_client, help_db, category, model, title_field, image_field
):
    _, session = help_db
    material_id = uuid.UUID(MOOD_HELP_MATERIALS[category][0].material_id)
    session.execute(
        update(model)
        .where(model.id == material_id)
        .values(
            **{
                title_field: "Updated in database",
                image_field: "https://cdn.example.com/updated.png",
            }
        )
    )
    session.commit()
    response = await help_client.get(f"/mood_tracker/help-categories/{category}")
    assert response.status_code == 200
    material = response.json()["materials"][0]
    assert material["title"] == "Updated in database"
    assert material["image_url"] == "https://cdn.example.com/updated.png"


@pytest.mark.asyncio
async def test_self_regulation_uses_existing_image_without_changing_database(
    help_client, help_db
):
    _, session = help_db
    reference = MOOD_HELP_MATERIALS["focus"][1]
    material = session.get(educationThemeOrm, uuid.UUID(reference.material_id))
    assert material.link_to_picture is None
    response = await help_client.get("/mood_tracker/help-categories/focus")
    assert response.status_code == 200
    assert response.json()["materials"][1]["image_url"] == (
        "/images/images_education_material/self-regulation.png"
    )
    session.refresh(material)
    assert material.link_to_picture is None


@pytest.mark.asyncio
@pytest.mark.parametrize("host", ["localhost", "api.example.com"])
async def test_help_image_paths_do_not_depend_on_request_host(help_client, host):
    response = await help_client.get(
        "/mood_tracker/help-categories/reflect", headers={"Host": host}
    )
    assert response.status_code == 200
    assert all(
        material["image_url"].startswith("/images/")
        for material in response.json()["materials"]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category,model",
    [
        ("reflect", QuestionnaireOrm),
        ("relax", educationThemeOrm),
        ("focus", ExerciseStructureOrm),
    ],
)
async def test_missing_help_material_returns_not_found(
    help_client, help_db, category, model
):
    _, session = help_db
    material_id = uuid.UUID(MOOD_HELP_MATERIALS[category][0].material_id)
    session.execute(delete(model).where(model.id == material_id))
    session.commit()
    response = await help_client.get(f"/mood_tracker/help-categories/{category}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unknown_help_category_returns_bad_request(help_client):
    response = await help_client.get("/mood_tracker/help-categories/unknown")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_help_category_list_keeps_existing_format(help_client):
    response = await help_client.get("/mood_tracker/help-categories")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ["reflect", "relax", "focus"]
    assert all(set(item) == {"id", "title"} for item in response.json())
