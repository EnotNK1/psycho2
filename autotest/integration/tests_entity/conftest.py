import pytest
import pytest_asyncio

from autotest.integration.postgres import create_integration_engine, create_session_factory, drop_test_schema, recreate_tables
from src.database import Base
from src.models.education import CardOrm, EducationProgressOrm, educationMaterialOrm, educationThemeOrm
from src.models.ontology import OntologyEntryOrm
from src.models.tests import (
    AnswerChoiceOrm,
    BordersOrm,
    QuestionOrm,
    ScaleOrm,
    ScaleResultOrm,
    TestOrm,
    TestResultOrm,
)
from src.models.users import UsersOrm
from src.utils.db_manager import DBManager


@pytest_asyncio.fixture
async def tests_entity_session_factory():
    engine = create_integration_engine()
    tables = [
        UsersOrm.__table__,
        OntologyEntryOrm.__table__,
        TestOrm.__table__,
        TestResultOrm.__table__,
        ScaleOrm.__table__,
        ScaleResultOrm.__table__,
        BordersOrm.__table__,
        QuestionOrm.__table__,
        AnswerChoiceOrm.__table__,
    ]
    await recreate_tables(engine, Base.metadata, tables)

    session_factory = create_session_factory(engine)
    try:
        yield session_factory
    finally:
        await drop_test_schema(engine)
        await engine.dispose()


@pytest_asyncio.fixture
async def tests_entity_db(tests_entity_session_factory):
    async with DBManager(tests_entity_session_factory) as db:
        yield db


@pytest.fixture
def tests_entity_db_manager_factory(tests_entity_session_factory):
    async def _manager():
        async with DBManager(tests_entity_session_factory) as db:
            yield db

    return _manager
