import pytest
import pytest_asyncio

from autotest.integration.postgres import create_integration_engine, create_session_factory, drop_test_schema, recreate_tables
from src.database import Base
from src.models.diary import DiaryOrm
from src.models.ontology import OntologyEntryOrm
from src.models.training_exercises import (
    TrainingCompletedExerciseOrm,
    TrainingExerciseOrm,
    TrainingQuestionOrm,
    TrainingVariantOrm,
)
from src.models.user_task import UserTaskOrm
from src.models.users import UsersOrm
from src.utils.db_manager import DBManager


@pytest_asyncio.fixture
async def integration_session_factory():
    engine = create_integration_engine()
    tables = [
        UsersOrm.__table__,
        OntologyEntryOrm.__table__,
        DiaryOrm.__table__,
        UserTaskOrm.__table__,
        TrainingExerciseOrm.__table__,
        TrainingQuestionOrm.__table__,
        TrainingVariantOrm.__table__,
        TrainingCompletedExerciseOrm.__table__,
    ]
    await recreate_tables(engine, Base.metadata, tables)

    session_factory = create_session_factory(engine)
    try:
        yield session_factory
    finally:
        await drop_test_schema(engine)
        await engine.dispose()


@pytest_asyncio.fixture
async def integration_db(integration_session_factory):
    async with DBManager(integration_session_factory) as db:
        yield db


@pytest.fixture
def integration_db_manager_factory(integration_session_factory):
    async def _manager():
        async with DBManager(integration_session_factory) as db:
            yield db

    return _manager
