import datetime
import uuid

import pytest
from sqlalchemy import select

from autotest.factories.exercise import (
    USER_ID,
    build_complete_payload,
    build_exercise_payload,
    build_field_payload,
    build_variant_payload,
    build_view_payload,
)
from src.models.exercise import CompletedExerciseOrm, ExerciseStructureOrm, FieldOrm, VariantOrm
from src.models.users import UsersOrm
from src.schemas.exercise import (
    CompletedExerciseCreate,
    ExerciseCreate,
    ExerciseViewCreate,
    FieldCreate,
    VariantCreate,
)
from src.services.exercise import ExerciseService


def build_user_orm(*, user_id=USER_ID):
    return UsersOrm(
        id=user_id,
        email="exercise-service@example.com",
        username="exercise-service-user",
        hashed_password="hashed",
        city="Tomsk",
        company=None,
        online=None,
        gender="male",
        birth_date=datetime.date(1999, 1, 1),
        phone_number="+70000000102",
        description=None,
        role_id=1,
        is_active=True,
        department=None,
        job_title=None,
        face_to_face=None,
    )


@pytest.mark.asyncio
async def test_exercise_service_create_and_get_all_from_real_db(exercise_db, exercise_session_factory):
    result = await ExerciseService(exercise_db).create_exercise(ExerciseCreate(**build_exercise_payload()))
    all_items = await ExerciseService(exercise_db).get_all_exercises(USER_ID)

    assert result.title == "Free writing"
    assert len(all_items) == 1
    assert all_items[0].id == result.id

    async with exercise_session_factory() as session:
        rows = (await session.execute(select(ExerciseStructureOrm))).scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_exercise_service_get_detail_marks_linked_exercise_open_after_previous_completion(
    exercise_db,
    exercise_session_factory,
):
    async with exercise_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    first = await ExerciseService(exercise_db).create_exercise(ExerciseCreate(**build_exercise_payload()))
    second = await ExerciseService(exercise_db).create_exercise(
        ExerciseCreate(**build_exercise_payload(title="Second", linked_exercise_id=first.id))
    )

    before = await ExerciseService(exercise_db).get_exercise_by_id(second.id, USER_ID)
    await ExerciseService(exercise_db).complete_exercise(
        USER_ID,
        CompletedExerciseCreate(exercise_structure_id=first.id, filled_fields=[]),
    )
    after = await ExerciseService(exercise_db).get_exercise_by_id(second.id, USER_ID)

    assert before.open is False
    assert after.open is True


@pytest.mark.asyncio
async def test_exercise_service_field_variant_structure_and_result_detail_real_db(
    exercise_db,
    exercise_session_factory,
):
    async with exercise_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    exercise = await ExerciseService(exercise_db).create_exercise(ExerciseCreate(**build_exercise_payload()))
    field = await ExerciseService(exercise_db).create_field(
        exercise.id,
        FieldCreate(**build_field_payload(exercises=None)),
    )
    variant = await ExerciseService(exercise_db).create_variant(
        field.id,
        VariantCreate(**build_variant_payload()),
    )
    await ExerciseService(exercise_db).create_exercise_view(
        exercise.id,
        ExerciseViewCreate(**build_view_payload(score=25)),
    )
    completed = await ExerciseService(exercise_db).complete_exercise(
        USER_ID,
        CompletedExerciseCreate(
            exercise_structure_id=exercise.id,
            filled_fields=[{"field_id": field.id, "text": "Real answer"}],
        ),
    )
    results = await ExerciseService(exercise_db).get_exercise_results(exercise.id, USER_ID)
    result_detail = await ExerciseService(exercise_db).get_exercise_result_detail(exercise.id, completed.id, USER_ID)

    assert variant.field_id == field.id
    assert completed.score == 25
    assert results.results[0].preview == "Real answer"
    assert result_detail.sections[0].value == "Real answer"

    async with exercise_session_factory() as session:
        fields = (await session.execute(select(FieldOrm))).scalars().all()
        variants = (await session.execute(select(VariantOrm))).scalars().all()
        completed_rows = (await session.execute(select(CompletedExerciseOrm))).scalars().all()
    assert len(fields) == 1
    assert len(variants) == 1
    assert len(completed_rows) == 1


@pytest.mark.asyncio
async def test_exercise_service_delete_resources_from_real_db(exercise_db, exercise_session_factory):
    exercise = await ExerciseService(exercise_db).create_exercise(ExerciseCreate(**build_exercise_payload()))
    field = await ExerciseService(exercise_db).create_field(
        exercise.id,
        FieldCreate(**build_field_payload(exercises=None)),
    )
    variant = await ExerciseService(exercise_db).create_variant(field.id, VariantCreate(**build_variant_payload()))

    await ExerciseService(exercise_db).delete_variant(variant.id)
    await ExerciseService(exercise_db).delete_field(field.id)
    await ExerciseService(exercise_db).delete_exercise(exercise.id)

    async with exercise_session_factory() as session:
        exercises = (await session.execute(select(ExerciseStructureOrm))).scalars().all()
        fields = (await session.execute(select(FieldOrm))).scalars().all()
        variants = (await session.execute(select(VariantOrm))).scalars().all()
    assert exercises == []
    assert fields == []
    assert variants == []


@pytest.mark.asyncio
async def test_exercise_service_missing_result_detail_raises_not_found(exercise_db):
    exercise = await ExerciseService(exercise_db).create_exercise(ExerciseCreate(**build_exercise_payload()))

    with pytest.raises(Exception) as exc_info:
        await ExerciseService(exercise_db).get_exercise_result_detail(exercise.id, uuid.uuid4(), USER_ID)

    assert getattr(exc_info.value, "status_code", None) == 404
