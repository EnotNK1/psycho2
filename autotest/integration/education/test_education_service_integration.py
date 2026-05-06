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
from src.services.education import EducationService


FIRST_THEME_ID = uuid.UUID("22cbb105-8857-48de-806d-7242ced60a97")
FIRST_MATERIAL_ID = uuid.UUID("cd9962af-94e6-4787-9842-9e263745804f")


@pytest.mark.asyncio
async def test_education_service_auto_create_persists_real_rows(
    education_db,
    education_session_factory,
):
    result = await EducationService(education_db).auto_create_education()

    assert result["status"] == "OK"

    async with education_session_factory() as session:
        themes = (await session.execute(select(educationThemeOrm))).scalars().all()
    assert len(themes) > 0


@pytest.mark.asyncio
async def test_education_service_get_theme_materials_returns_cards_and_recommendations(
    education_db,
    education_session_factory,
):
    from autotest.integration.education.conftest import build_user_orm

    await EducationService(education_db).auto_create_education()
    async with education_session_factory() as session:
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

    result = await EducationService(education_db).get_education_theme_materials(FIRST_THEME_ID, USER_ID)

    assert result.id == FIRST_THEME_ID
    assert len(result.recommendations) > 0
    assert len(result.education_materials) > 0
    assert len(result.education_materials[0].cards) > 0


@pytest.mark.asyncio
async def test_education_service_complete_material_creates_progress_and_score(
    education_db,
    education_session_factory,
):
    from autotest.integration.education.conftest import build_user_orm

    await EducationService(education_db).auto_create_education()
    async with education_session_factory() as session:
        session.add(build_user_orm(USER_ID))
        await session.commit()

    await EducationService(education_db).complete_education_material(
        type("Payload", (), {"education_material_id": FIRST_MATERIAL_ID})(),
        USER_ID,
    )

    async with education_session_factory() as session:
        progress_rows = (await session.execute(select(EducationProgressOrm))).scalars().all()
        score_rows = (await session.execute(select(UserScoreOrm))).scalars().all()

    assert len(progress_rows) == 1
    assert progress_rows[0].education_material_id == FIRST_MATERIAL_ID
    assert progress_rows[0].user_id == USER_ID
    assert len(score_rows) == 1
    assert score_rows[0].score == 10


@pytest.mark.asyncio
async def test_education_service_complete_material_raises_duplicate_on_second_completion(
    education_db,
    education_session_factory,
):
    from autotest.integration.education.conftest import build_user_orm

    await EducationService(education_db).auto_create_education()
    async with education_session_factory() as session:
        session.add(build_user_orm(USER_ID))
        await session.commit()

    payload = type("Payload", (), {"education_material_id": FIRST_MATERIAL_ID})()
    await EducationService(education_db).complete_education_material(payload, USER_ID)

    with pytest.raises(Exception) as exc_info:
        await EducationService(education_db).complete_education_material(payload, USER_ID)

    assert exc_info.value.__class__.__name__ == "ObjectAlreadyExistsException"


@pytest.mark.asyncio
async def test_education_service_complete_theme_marks_daily_task_complete(
    education_db,
    education_session_factory,
):
    from autotest.integration.education.conftest import build_user_orm

    async with education_session_factory() as session:
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

    await EducationService(education_db).complete_education_theme(
        type("Payload", (), {"education_theme_id": FIRST_THEME_ID})(),
        USER_ID,
    )

    async with education_session_factory() as session:
        task = (await session.execute(select(DailyTaskOrm).where(DailyTaskOrm.id == DAILY_TASK_ID))).scalar_one()
    assert task.is_complete is True


@pytest.mark.asyncio
async def test_education_service_get_user_progress_returns_only_target_user_rows(
    education_db,
    education_session_factory,
):
    from autotest.integration.education.conftest import build_user_orm

    await EducationService(education_db).auto_create_education()
    async with education_session_factory() as session:
        session.add(build_user_orm(USER_ID))
        session.add(build_user_orm(SECOND_USER_ID))
        session.add(
            EducationProgressOrm(
                id=uuid.uuid4(),
                user_id=USER_ID,
                education_material_id=FIRST_MATERIAL_ID,
            )
        )
        session.add(
            EducationProgressOrm(
                id=uuid.uuid4(),
                user_id=SECOND_USER_ID,
                education_material_id=FIRST_MATERIAL_ID,
            )
        )
        await session.commit()

    result = await EducationService(education_db).get_user_progress(USER_ID)

    assert len(result) == 1
    assert result[0].user_id == USER_ID
    assert result[0].education_material_id == FIRST_MATERIAL_ID
