from datetime import datetime

import pytest
from sqlalchemy import select

from autotest4.factories.diary import DIARY_ID, USER_ID
from src.models.diary import DiaryOrm
from src.services.diary import DiaryService


def build_diary_orm(
    *,
    diary_id=DIARY_ID,
    text="Diary from DB",
    created_at=datetime(2026, 4, 10, 10, 0, 0),
    user_id=USER_ID,
):
    return DiaryOrm(
        id=diary_id,
        text=text,
        created_at=created_at,
        user_id=user_id,
    )


@pytest.mark.asyncio
async def test_diary_service_add_and_get_integration(integration_db, integration_session_factory):
    await DiaryService(integration_db).add_diary(type("Req", (), {"text": "Service diary", "day": "2024-04-10"})(), USER_ID)

    diaries = await DiaryService(integration_db).get_diary(USER_ID)

    assert diaries[0].text == "Service diary"

    async with integration_session_factory() as session:
        result = await session.execute(select(DiaryOrm).filter_by(user_id=USER_ID))
        stored = result.scalars().one()
        assert stored.text == "Service diary"


@pytest.mark.asyncio
async def test_diary_service_get_by_day_and_month_integration(integration_db, integration_session_factory):
    async with integration_session_factory() as session:
        session.add(build_diary_orm(created_at=datetime(2026, 4, 10, 9, 0, 0)))
        session.add(build_diary_orm(diary_id=__import__("uuid").uuid4(), created_at=datetime(2026, 4, 20, 9, 0, 0)))
        await session.commit()

    by_day = await DiaryService(integration_db).get_diary(USER_ID, "2026-04-10")
    by_month = await DiaryService(integration_db).get_diary_for_month(1775001600, USER_ID)

    assert len(by_day) == 1
    assert by_day[0].id == DIARY_ID
    assert by_month[9]["diary"] is True
    assert by_month[19]["diary"] is True
