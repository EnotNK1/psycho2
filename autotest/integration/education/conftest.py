import datetime

import pytest
import pytest_asyncio

import src.api.education as education_api_module
from autotest.integration.postgres import create_integration_engine, create_session_factory, drop_test_schema, recreate_tables
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.database import Base
from src.models.daily_tasks import DailyTaskOrm
from src.models.education import CardOrm, EducationProgressOrm, educationMaterialOrm, educationThemeOrm
from src.models.gamification import UserScoreOrm
from src.models.ontology import OntologyEntryOrm
from src.models.users import UsersOrm
from src.utils.db_manager import DBManager


@pytest_asyncio.fixture
async def education_session_factory():
    engine = create_integration_engine()
    tables = [
        UsersOrm.__table__,
        OntologyEntryOrm.__table__,
        educationThemeOrm.__table__,
        educationMaterialOrm.__table__,
        CardOrm.__table__,
        EducationProgressOrm.__table__,
        UserScoreOrm.__table__,
        DailyTaskOrm.__table__,
    ]
    await recreate_tables(engine, Base.metadata, tables)

    session_factory = create_session_factory(engine)
    try:
        yield session_factory
    finally:
        await drop_test_schema(engine)
        await engine.dispose()


@pytest_asyncio.fixture
async def education_db(education_session_factory):
    async with DBManager(education_session_factory) as db:
        yield db


@pytest.fixture
def education_db_manager_factory(education_session_factory):
    async def _manager():
        async with DBManager(education_session_factory) as db:
            yield db

    return _manager


@pytest.fixture
def education_integration_client_factory(api_client_factory, education_db_manager_factory):
    def _factory(user_id):
        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                education_api_module.router,
                dependency_overrides={
                    get_db: education_db_manager_factory,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client

        return _client()

    return _factory


def build_user_orm(user_id):
    return UsersOrm(
        id=user_id,
        email=f"education-{str(user_id)[:8]}@example.com",
        username=f"education-{str(user_id)[:8]}",
        hashed_password="hashed",
        city="Tomsk",
        company=None,
        online=None,
        gender="male",
        birth_date=datetime.date(1999, 1, 1),
        phone_number="+70000000004",
        description=None,
        role_id=1,
        is_active=True,
        department=None,
        job_title=None,
        face_to_face=None,
    )
