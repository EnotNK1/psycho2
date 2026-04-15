from sqlalchemy import select

import pytest

import src.services.auth as auth_service_module
from autotest4.factories.auth import USER_ID
from src.models.ontology import OntologyEntryOrm
from src.models.users import UsersOrm
from src.services.auth import AuthService


class DummyDailyTaskService:
    def __init__(self, db):
        self.db = db

    async def add_daily_tasks_for_new_user(self, user_id):
        return {"status": "OK"}


@pytest.mark.asyncio
async def test_auth_service_register_and_login_integration(integration_db, integration_session_factory, monkeypatch):
    monkeypatch.setattr(auth_service_module, "DailyTaskService", DummyDailyTaskService)
    service = AuthService(integration_db)

    data = type(
        "RegisterPayload",
        (),
        {
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
            "model_dump": lambda self, exclude=None: {
                "email": "user@example.com",
                "username": "tester",
                "birth_date": __import__("datetime").date(1999, 1, 1),
                "gender": "male",
                "city": "Tomsk",
                "phone_number": "+70000000000",
            },
        },
    )()

    access_token, refresh_token = await service.register_user(data)
    assert access_token
    assert refresh_token

    login_access_token, login_refresh_token = await service.login_user(
        type("LoginPayload", (), {"email": "user@example.com", "password": "StrongPass123"})()
    )
    assert login_access_token
    assert login_refresh_token

    async with integration_session_factory() as session:
        result = await session.execute(select(UsersOrm).filter_by(email="user@example.com"))
        assert result.scalars().one_or_none() is not None


@pytest.mark.asyncio
async def test_auth_service_get_ontology_integration(integration_db, integration_session_factory):
    async with integration_session_factory() as session:
        session.add(
            OntologyEntryOrm(
                id=USER_ID,
                type="theme",
                created_at=__import__("datetime").datetime(2026, 4, 10, 12, 0, 0),
                destination_id=USER_ID,
                destination_title="Material",
                link_to_picture="/img.png",
                user_id=USER_ID,
            )
        )
        await session.commit()

    result = await AuthService(integration_db).get_ontology(USER_ID)

    assert len(result) == 1
    assert result[0].type == "theme"
    assert result[0].destination_id == USER_ID
