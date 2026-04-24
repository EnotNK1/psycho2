import pytest
import pytest_asyncio

from autotest.integration.postgres import create_integration_engine, create_session_factory, drop_test_schema, recreate_tables
from src.database import Base
from src.models.exercise import (
    CompletedExerciseOrm,
    ExerciseStructureOrm,
    ExerciseViewOrm,
    FieldOrm,
    FilledFieldOrm,
    VariantOrm,
)
from src.models.ontology import OntologyEntryOrm
from src.models.users import UsersOrm
from src.utils.db_manager import DBManager


@pytest_asyncio.fixture
async def exercise_session_factory():
    engine = create_integration_engine()
    tables = [
        UsersOrm.__table__,
        OntologyEntryOrm.__table__,
        ExerciseStructureOrm.__table__,
        FieldOrm.__table__,
        VariantOrm.__table__,
        ExerciseViewOrm.__table__,
        CompletedExerciseOrm.__table__,
        FilledFieldOrm.__table__,
    ]
    await recreate_tables(engine, Base.metadata, tables)

    session_factory = create_session_factory(engine)
    try:
        yield session_factory
    finally:
        await drop_test_schema(engine)
        await engine.dispose()


@pytest_asyncio.fixture
async def exercise_db(exercise_session_factory):
    async with DBManager(exercise_session_factory) as db:
        yield db


@pytest.fixture
def exercise_db_manager_factory(exercise_session_factory):
    async def _manager():
        async with DBManager(exercise_session_factory) as db:
            yield db

    return _manager
