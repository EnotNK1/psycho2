import datetime
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import src.services.exercise as exercise_service_module
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
    ExerciseUpdate,
    ExerciseViewCreate,
    ExerciseViewUpdate,
    FieldCreate,
    FieldUpdate,
    VariantCreate,
    VariantUpdate,
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
    assert result.sort_order == 1
    assert len(all_items["regular_exercises"]) == 1
    assert all_items["regular_exercises"][0].id == result.id
    assert all_items["related_exercises"] == []

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
async def test_exercise_service_update_resources_in_real_db(exercise_db, exercise_session_factory):
    exercise = await ExerciseService(exercise_db).create_exercise(ExerciseCreate(**build_exercise_payload()))
    field = await ExerciseService(exercise_db).create_field(
        exercise.id,
        FieldCreate(**build_field_payload(exercises=None)),
    )
    variant = await ExerciseService(exercise_db).create_variant(
        field.id,
        VariantCreate(**build_variant_payload()),
    )
    view = await ExerciseService(exercise_db).create_exercise_view(
        exercise.id,
        ExerciseViewCreate(**build_view_payload()),
    )

    updated_exercise = await ExerciseService(exercise_db).update_exercise(
        exercise.id,
        ExerciseUpdate(title="Updated exercise"),
    )
    updated_field = await ExerciseService(exercise_db).update_field(
        field.id,
        FieldUpdate(title="Updated field", order=2),
    )
    updated_variant = await ExerciseService(exercise_db).update_variant(
        variant.id,
        VariantUpdate(title="Updated variant"),
    )
    updated_view = await ExerciseService(exercise_db).update_exercise_view(
        view.id,
        ExerciseViewUpdate(message="Updated view message", score=77),
    )

    assert updated_exercise.title == "Updated exercise"
    assert updated_exercise.sort_order == 1
    assert updated_field.title == "Updated field"
    assert updated_field.order == 2
    assert updated_field.position == 1
    assert updated_variant.title == "Updated variant"
    assert updated_view.message == "Updated view message"
    assert updated_view.score == 77

    async with exercise_session_factory() as session:
        exercise_row = await session.get(ExerciseStructureOrm, exercise.id)
        field_row = await session.get(FieldOrm, field.id)
        variant_row = await session.get(VariantOrm, variant.id)

    assert exercise_row.title == "Updated exercise"
    assert field_row.title == "Updated field"
    assert variant_row.title == "Updated variant"


@pytest.mark.asyncio
async def test_exercise_service_seed_exercises_updates_existing_fixture_data(
    exercise_db, exercise_session_factory, monkeypatch
):
    seeded_id = uuid.uuid4()
    first_field_id = uuid.uuid4()
    second_field_id = uuid.uuid4()

    monkeypatch.setattr(
        exercise_service_module,
        "EXERCISES",
        [
            {
                "id": str(seeded_id),
                "title": "Seed v1",
                "description": "First version",
                "picture_link": "/images/v1.png",
                "time_to_read": 5,
                "questions_count": 1,
                "sort_order": 1,
                "linked_exercise_id": None,
                "fields": [
                    {
                        "id": str(first_field_id),
                        "title": "Field v1",
                        "major": True,
                        "view": "default",
                        "type": "input",
                        "placeholder": "v1",
                        "prompt": "",
                        "description": "",
                        "order": 0,
                        "position": 1,
                        "variants": [],
                    }
                ],
                "views": [],
            }
        ],
    )
    await ExerciseService(exercise_db).seed_exercises()
    await exercise_db.commit()

    monkeypatch.setattr(
        exercise_service_module,
        "EXERCISES",
        [
            {
                "id": str(seeded_id),
                "title": "Seed v2",
                "description": "Second version",
                "picture_link": "/images/v2.png",
                "time_to_read": 7,
                "questions_count": 2,
                "sort_order": 2,
                "linked_exercise_id": None,
                "fields": [
                    {
                        "id": str(second_field_id),
                        "title": "Field v2",
                        "major": False,
                        "view": "primary",
                        "type": "input",
                        "placeholder": "v2",
                        "prompt": "",
                        "description": "",
                        "order": 1,
                        "position": 1,
                        "variants": [],
                    }
                ],
                "views": [],
            }
        ],
    )
    await ExerciseService(exercise_db).seed_exercises()
    await exercise_db.commit()

    async with exercise_session_factory() as session:
        exercise_row = await session.get(ExerciseStructureOrm, seeded_id)
        fields = (
            await session.execute(
                select(FieldOrm).where(FieldOrm.exercise_structure_id == seeded_id)
            )
        ).scalars().all()

    assert exercise_row.title == "Seed v2"
    assert exercise_row.picture_link == "/images/v2.png"
    assert exercise_row.sort_order == 2
    assert exercise_row.group == 1
    assert len(fields) == 1
    assert fields[0].id == second_field_id
    assert fields[0].title == "Field v2"
    assert fields[0].position == 1


@pytest.mark.asyncio
async def test_exercise_service_get_all_splits_regular_and_related_groups(exercise_db):
    regular = await ExerciseService(exercise_db).create_exercise(
        ExerciseCreate(**build_exercise_payload(title="Regular", group=1, sort_order=1))
    )
    related = await ExerciseService(exercise_db).create_exercise(
        ExerciseCreate(**build_exercise_payload(title="Related", group=2, sort_order=2))
    )

    result = await ExerciseService(exercise_db).get_all_exercises(USER_ID)

    assert [item.id for item in result["regular_exercises"]] == [regular.id]
    assert [item.id for item in result["related_exercises"]] == [related.id]


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


@pytest.mark.asyncio
async def test_exercise_service_groups_pulled_fields_and_preserves_links_in_results(
    exercise_db,
    exercise_session_factory,
):
    async with exercise_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    source = await ExerciseService(exercise_db).create_exercise(
        ExerciseCreate(**build_exercise_payload(title="Source"))
    )
    target = await ExerciseService(exercise_db).create_exercise(
        ExerciseCreate(
            **build_exercise_payload(
                title="Target",
                linked_exercise_id=source.id,
                sort_order=2,
            )
        )
    )

    source_field_one = await ExerciseService(exercise_db).create_field(
        source.id,
        FieldCreate(
            **build_field_payload(
                title="Source one",
                pull_group="memory_pair",
                exercises=[target.id],
            )
        ),
    )
    source_field_two = await ExerciseService(exercise_db).create_field(
        source.id,
        FieldCreate(
            **build_field_payload(
                title="Source two",
                order=1,
                position=2,
                pull_group="memory_pair",
                exercises=[target.id],
            )
        ),
    )
    target_field = await ExerciseService(exercise_db).create_field(
        target.id,
        FieldCreate(**build_field_payload(exercises=None)),
    )

    await ExerciseService(exercise_db).complete_exercise(
        USER_ID,
        CompletedExerciseCreate(
            exercise_structure_id=source.id,
            filled_fields=[
                {"field_id": source_field_one.id, "text": "Source A1"},
                {"field_id": source_field_two.id, "text": "Source A2"},
            ],
        ),
    )
    await ExerciseService(exercise_db).complete_exercise(
        USER_ID,
        CompletedExerciseCreate(
            exercise_structure_id=source.id,
            filled_fields=[
                {"field_id": source_field_one.id, "text": "Source B1"},
                {"field_id": source_field_two.id, "text": "Source B2"},
            ],
        ),
    )

    structure = await ExerciseService(exercise_db).get_exercise_structure_by_id(
        target.id,
        USER_ID,
    )

    assert len(structure.pulled_fields) == 2
    assert all(group.source_group_key == "memory_pair" for group in structure.pulled_fields)
    assert all(len(group.fields) == 2 for group in structure.pulled_fields)

    completion = await ExerciseService(exercise_db).complete_exercise(
        USER_ID,
        CompletedExerciseCreate(
            exercise_structure_id=target.id,
            filled_fields=[
                {
                    "field_id": target_field.id,
                    "text": "Target for first pair",
                    "pulled_completed_exercise_id": structure.pulled_fields[0].source_completed_exercise_id,
                    "pulled_group_key": structure.pulled_fields[0].source_group_key,
                },
                {
                    "field_id": target_field.id,
                    "text": "Target for second pair",
                    "pulled_completed_exercise_id": structure.pulled_fields[1].source_completed_exercise_id,
                    "pulled_group_key": structure.pulled_fields[1].source_group_key,
                },
            ],
        ),
    )

    detail = await ExerciseService(exercise_db).get_exercise_result_detail(
        target.id,
        completion.id,
        USER_ID,
    )

    assert len(detail.sections) == 2
    assert detail.sections[0].pulled_group_key == "memory_pair"
    assert len(detail.sections[0].pulled_fields) == 2
    assert {
        item.text for item in detail.sections[0].pulled_fields
    } in (
        {"Source A1", "Source A2"},
        {"Source B1", "Source B2"},
    )

    async with exercise_session_factory() as session:
        filled_rows = (
            await session.execute(
                select(CompletedExerciseOrm).where(
                    CompletedExerciseOrm.id == completion.id
                ).options(selectinload(CompletedExerciseOrm.filled_field))
            )
        ).scalars().one()

    assert len(filled_rows.filled_field) == 2
