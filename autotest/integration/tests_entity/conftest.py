import pytest
import pytest_asyncio
from sqlalchemy import JSON
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

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
async def tests_entity_session_factory(tmp_path):
    db_path = tmp_path / "integration_tests_entity.sqlite3"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)

    original_type = QuestionOrm.__table__.c.answer_choice.type
    QuestionOrm.__table__.c.answer_choice.type = JSON()

    try:
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn,
                    tables=[
                        UsersOrm.__table__,
                        OntologyEntryOrm.__table__,
                        TestOrm.__table__,
                        TestResultOrm.__table__,
                        ScaleOrm.__table__,
                        ScaleResultOrm.__table__,
                        BordersOrm.__table__,
                        QuestionOrm.__table__,
                        AnswerChoiceOrm.__table__,
                    ],
                )
            )

        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        try:
            yield session_factory
        finally:
            await engine.dispose()
    finally:
        QuestionOrm.__table__.c.answer_choice.type = original_type


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
