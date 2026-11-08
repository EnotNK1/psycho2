import importlib.util
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from src.services.exercise import ExerciseService
from src.services.fixtures.exercise import EXERCISES


EXPECTED_FIELDS = {
    "5f81cc8b-b057-47cb-96af-a0839d6c0ad9": [
        "682a4479-5693-48ae-abe1-df6b899f08df",
        "300d244f-3ac9-48e0-a962-6655004914e7",
        "836d8f33-4587-4887-a225-0a6388aea7e2",
    ],
    "4e3f51e9-aad8-4a13-b4b7-d748e472d394": [
        "4592b3e9-cbd8-4ec2-bed7-e29015cb4db5",
        "8e4e8a0d-d473-46ca-8dec-a6b3ffac69bd",
        "983686f3-83cd-493a-b485-8c428eafaddb",
        "ee2fb3da-472a-4478-808a-9f1ab7ff81b7",
    ],
}


def load_migration():
    path = Path(
        "src/migrations/versions/2026_10_27_1400-d3e6a8b2c4f0_fix_exercise_situation_field_order.py"
    )
    spec = importlib.util.spec_from_file_location("exercise_field_order_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


@pytest.mark.parametrize("exercise_id", EXPECTED_FIELDS)
def test_structure_starts_with_situation_despite_database_row_order(exercise_id):
    fixture = next(item for item in EXERCISES if item["id"] == exercise_id)
    exercise = SimpleNamespace(**{
        key: value for key, value in fixture.items() if key not in ("fields", "views")
    })
    exercise.field = [SimpleNamespace(**field) for field in reversed(fixture["fields"])]
    result = ExerciseService()._to_exercise_structure_response(exercise, True, [])
    first_page = result.pages[0]
    assert first_page.page_number == 0
    assert [str(section.id) for section in first_page.sections] == EXPECTED_FIELDS[exercise_id]
    assert first_page.sections[0].title.startswith("Опишите ситуацию")
    assert [section.position for section in first_page.sections] == list(
        range(1, len(first_page.sections) + 1)
    )
    assert sum(len(page.sections) for page in result.pages) == len(fixture["fields"])


@pytest.fixture
def migration_db():
    migration = load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    metadata = sa.MetaData()
    field = sa.Table(
        "field", metadata,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("exercise_structure_id", sa.Uuid()),
        sa.Column("position", sa.Integer()),
        sa.Column("order", sa.Integer()),
        sa.Column("title", sa.String()),
    )
    filled = sa.Table(
        "filled_field", metadata,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("field_id", sa.Uuid()),
        sa.Column("text", sa.Text()),
    )
    metadata.create_all(engine)
    with engine.begin() as connection:
        for exercise_id, field_id, original, _ in migration.FIELD_POSITIONS:
            connection.execute(field.insert().values(
                id=uuid.UUID(field_id), exercise_structure_id=uuid.UUID(exercise_id),
                position=original, order=0, title="Keep original title",
            ))
            connection.execute(filled.insert().values(
                id=uuid.uuid4(), field_id=uuid.UUID(field_id), text="enc::preserve-answer",
            ))
        unrelated_id = uuid.uuid4()
        connection.execute(field.insert().values(
            id=unrelated_id, exercise_structure_id=uuid.uuid4(), position=17,
            order=4, title="Unrelated field",
        ))
        yield migration, connection, field, filled
    engine.dispose()


def test_migration_updates_only_positions_and_preserves_answers(migration_db):
    migration, connection, field, filled = migration_db
    before = {row["id"]: dict(row) for row in connection.execute(sa.select(field)).mappings()}
    answers = list(connection.execute(sa.select(filled)).mappings())
    with Operations.context(MigrationContext.configure(connection)):
        migration.upgrade()
    after = {row["id"]: dict(row) for row in connection.execute(sa.select(field)).mappings()}
    expected = {uuid.UUID(fid): updated for _, fid, _, updated in migration.FIELD_POSITIONS}
    assert before.keys() == after.keys()
    for field_id, old in before.items():
        assert after[field_id] == {**old, "position": expected.get(field_id, old["position"])}
    assert list(connection.execute(sa.select(filled)).mappings()) == answers


def test_migration_is_repeatable_and_downgrade_restores_positions(migration_db):
    migration, connection, field, _ = migration_db
    before = list(connection.execute(sa.select(field).order_by(field.c.id)).mappings())
    with Operations.context(MigrationContext.configure(connection)):
        migration.upgrade()
        once = list(connection.execute(sa.select(field).order_by(field.c.id)).mappings())
        migration.upgrade()
        assert list(connection.execute(sa.select(field).order_by(field.c.id)).mappings()) == once
        migration.downgrade()
    assert list(connection.execute(sa.select(field).order_by(field.c.id)).mappings()) == before


def test_migration_is_safe_when_the_exercises_have_not_been_seeded():
    migration = load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    metadata = sa.MetaData()
    field = sa.Table(
        "field", metadata,
        sa.Column("id", sa.Uuid()), sa.Column("exercise_structure_id", sa.Uuid()),
        sa.Column("position", sa.Integer()),
    )
    metadata.create_all(engine)
    with engine.begin() as connection:
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert connection.execute(sa.select(sa.func.count()).select_from(field)).scalar_one() == 0
    engine.dispose()


def test_migration_positions_match_seed_data():
    migration = load_migration()
    fixture_fields = {
        (exercise["id"], field["id"]): field
        for exercise in EXERCISES for field in exercise["fields"]
    }
    for exercise_id, field_id, _, position in migration.FIELD_POSITIONS:
        assert fixture_fields[(exercise_id, field_id)]["position"] == position
