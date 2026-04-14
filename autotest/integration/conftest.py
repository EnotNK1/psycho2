import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

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
async def integration_session_factory(tmp_path):
    db_path = tmp_path / "integration_auth.sqlite3"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    UsersOrm.__table__,
                    OntologyEntryOrm.__table__,
                    DiaryOrm.__table__,
                    UserTaskOrm.__table__,
                    TrainingExerciseOrm.__table__,
                    TrainingQuestionOrm.__table__,
                    TrainingVariantOrm.__table__,
                    TrainingCompletedExerciseOrm.__table__,
                ],
            )
        )

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield session_factory
    finally:
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
