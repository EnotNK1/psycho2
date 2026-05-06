import datetime
import uuid

import pytest
from sqlalchemy import select

from autotest.factories.education import DAILY_TASK_ID, SECOND_USER_ID, USER_ID
from src.enums import DailyTaskType
from src.models.daily_tasks import DailyTaskOrm
from src.models.education import EducationProgressOrm, educationThemeOrm
from src.models.gamification import UserScoreOrm
from src.models.ontology import OntologyEntryOrm


FIRST_THEME_ID = uuid.UUID("22cbb105-8857-48de-806d-7242ced60a97")
FIRST_MATERIAL_ID = uuid.UUID("cd9962af-94e6-4787-9842-9e263745804f")


@pytest.mark.asyncio
async def test_education_auto_create_and_list_themes_integration(
    education_integration_client_factory,
    education_session_factory,
):
    async with education_session_factory() as session:
        from autotest.integration.education.conftest import build_user_orm

        session.add(build_user_orm(USER_ID))
        await session.commit()

    async for client in education_integration_client_factory(USER_ID):
        seed_response = await client.post("/education/auto-create")
        list_response = await client.get("/education/themes/all")

    assert seed_response.status_code == 200
    assert seed_response.json()["status"] == "OK"
    assert list_response.status_code == 200
    assert len(list_response.json()) > 0
    assert len(list_response.json()[0]["education_materials"]) > 0
    assert "cards" in list_response.json()[0]["education_materials"][0]

    async with education_session_factory() as session:
        rows = (await session.execute(select(educationThemeOrm))).scalars().all()
    assert len(rows) > 0


@pytest.mark.asyncio
async def test_education_theme_materials_returns_recommendations_and_clears_ontology_integration(
    education_integration_client_factory,
    education_session_factory,
):
    async with education_session_factory() as session:
        from autotest.integration.education.conftest import build_user_orm

        session.add(build_user_orm(USER_ID))
        session.add(
            OntologyEntryOrm(
                id=uuid.uuid4(),
                type="education",
                created_at=datetime.datetime(2026, 5, 6, 10, 0, 0),
                destination_id=FIRST_THEME_ID,
                destination_title="Theme",
                link_to_picture="/images/theme.png",
                user_id=USER_ID,
            )
        )
        await session.commit()

    async for client in education_integration_client_factory(USER_ID):
        await client.post("/education/auto-create")
        response = await client.get(f"/education/themes/{FIRST_THEME_ID}/materials/list")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(FIRST_THEME_ID)
    assert len(body["recommendations"]) > 0
    assert len(body["education_materials"]) > 0
    assert len(body["education_materials"][0]["cards"]) > 0

    async with education_session_factory() as session:
        rows = (await session.execute(select(OntologyEntryOrm).where(OntologyEntryOrm.user_id == USER_ID))).scalars().all()
    assert rows == []


@pytest.mark.asyncio
async def test_education_theme_materials_returns_404_for_missing_theme_integration(
    education_integration_client_factory,
):
    missing_id = uuid.uuid4()

    async for client in education_integration_client_factory(USER_ID):
        response = await client.get(f"/education/themes/{missing_id}/materials/list")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_complete_education_material_creates_progress_and_score_integration(
    education_integration_client_factory,
    education_session_factory,
):
    async with education_session_factory() as session:
        from autotest.integration.education.conftest import build_user_orm

        session.add(build_user_orm(USER_ID))
        await session.commit()

    async for client in education_integration_client_factory(USER_ID):
        await client.post("/education/auto-create")
        response = await client.post("/education/materials/complete", json={"education_material_id": str(FIRST_MATERIAL_ID)})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    async with education_session_factory() as session:
        progress_rows = (await session.execute(select(EducationProgressOrm))).scalars().all()
        score_rows = (await session.execute(select(UserScoreOrm))).scalars().all()

    assert len(progress_rows) == 1
    assert progress_rows[0].user_id == USER_ID
    assert progress_rows[0].education_material_id == FIRST_MATERIAL_ID
    assert len(score_rows) == 1
    assert score_rows[0].score == 10


@pytest.mark.asyncio
async def test_complete_education_material_returns_409_for_duplicate_integration(
    education_integration_client_factory,
    education_session_factory,
):
    async with education_session_factory() as session:
        from autotest.integration.education.conftest import build_user_orm

        session.add(build_user_orm(USER_ID))
        await session.commit()

    async for client in education_integration_client_factory(USER_ID):
        await client.post("/education/auto-create")
        first_response = await client.post("/education/materials/complete", json={"education_material_id": str(FIRST_MATERIAL_ID)})
        second_response = await client.post("/education/materials/complete", json={"education_material_id": str(FIRST_MATERIAL_ID)})

    assert first_response.status_code == 200
    assert second_response.status_code == 409


@pytest.mark.asyncio
async def test_complete_education_material_returns_404_for_missing_material_integration(
    education_integration_client_factory,
    education_session_factory,
):
    async with education_session_factory() as session:
        from autotest.integration.education.conftest import build_user_orm

        session.add(build_user_orm(USER_ID))
        await session.commit()

    async for client in education_integration_client_factory(USER_ID):
        response = await client.post("/education/materials/complete", json={"education_material_id": str(uuid.uuid4())})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_complete_education_theme_marks_daily_task_completed_integration(
    education_integration_client_factory,
    education_session_factory,
):
    async with education_session_factory() as session:
        from autotest.integration.education.conftest import build_user_orm

        session.add(build_user_orm(USER_ID))
        await session.commit()
        session.add(
            DailyTaskOrm(
                id=DAILY_TASK_ID,
                title="Read theme",
                short_desc="Read educational theme",
                destination_id=FIRST_THEME_ID,
                number=1,
                day=1,
                is_complete=False,
                is_current=True,
                type=DailyTaskType.THEORY,
                user_id=USER_ID,
            )
        )
        await session.commit()

    async for client in education_integration_client_factory(USER_ID):
        response = await client.post("/education/themes/complete", json={"education_theme_id": str(FIRST_THEME_ID)})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    async with education_session_factory() as session:
        task = (
            await session.execute(select(DailyTaskOrm).where(DailyTaskOrm.id == DAILY_TASK_ID))
        ).scalar_one()
    assert task.is_complete is True


@pytest.mark.asyncio
async def test_get_user_progress_returns_only_current_user_rows_integration(
    education_integration_client_factory,
    education_session_factory,
):
    async with education_session_factory() as session:
        from autotest.integration.education.conftest import build_user_orm

        session.add(build_user_orm(USER_ID))
        session.add(build_user_orm(SECOND_USER_ID))
        await session.commit()

    async for client in education_integration_client_factory(USER_ID):
        await client.post("/education/auto-create")
        await client.post("/education/materials/complete", json={"education_material_id": str(FIRST_MATERIAL_ID)})

    async with education_session_factory() as session:
        session.add(
            EducationProgressOrm(
                id=uuid.uuid4(),
                user_id=SECOND_USER_ID,
                education_material_id=FIRST_MATERIAL_ID,
            )
        )
        await session.commit()

    async for client in education_integration_client_factory(USER_ID):
        response = await client.get("/education/progress")

    assert response.status_code == 200
    assert response.json() == [{"user_id": str(USER_ID), "education_material_id": str(FIRST_MATERIAL_ID)}]
