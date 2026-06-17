import pytest

import src.services.exercise as exercise_service_module
from src.services.fixtures.exercise import EXERCISES as FIXTURE_EXERCISES
from autotest.factories.exercise import (
    EXERCISE_ID,
    FIELD_ID,
    RESULT_ID,
    SECOND_EXERCISE_ID,
    SECOND_FIELD_ID,
    USER_ID,
    VARIANT_ID,
    VIEW_ID,
    build_complete_payload,
    build_completed_response,
    build_completed_exercise_list_item,
    build_exercise_detail_response,
    build_exercise_payload,
    build_exercise_response,
    build_field_payload,
    build_field_response,
    build_result_detail_response,
    build_results_response,
    build_structure_response,
    build_variant_payload,
    build_variant_response,
    build_view_payload,
    build_view_response,
    make_completed_orm_like,
    make_exercise_orm_like,
    make_field_orm_like,
    make_filled_field_orm_like,
    make_variant_orm_like,
)
from src.exceptions import MyAppException, ObjectAlreadyExistsException, ObjectNotFoundHTTPException
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


class FakeExerciseRepository:
    def __init__(self):
        self.one_or_none_result = None
        self.added = []
        self.exercise_entity = make_exercise_orm_like(
            fields=[make_field_orm_like(variants=[make_variant_orm_like()])]
        )
        self.field = make_field_orm_like(variants=[])
        self.variant = make_variant_orm_like()
        self.view = type(
            "ExerciseView",
            (),
            {
                "id": VIEW_ID,
                "view": "success",
                "score": 10,
                "picture_link": "/images/success.png",
                "message": "Exercise completed",
            },
        )()
        self.all_exercises = [self.exercise_entity]
        self.results = [make_completed_orm_like(filled_fields=[make_filled_field_orm_like()])]
        self.result_detail_rows = [
            (self.results[0], make_filled_field_orm_like(), self.field)
        ]
        self.passed_exercises = [
            (
                EXERCISE_ID,
                "Free writing",
                "/images/exercise.png",
                "2026-04-20T16:16:36.303731",
            )
        ]
        self.pulled_fields_rows = []
        self.calls = []
        self.raise_on = {}

    def _maybe_raise(self, method):
        error = self.raise_on.get(method)
        if error:
            raise error

    async def get_one_or_none(self, **kwargs):
        self.calls.append(("get_one_or_none", kwargs))
        self._maybe_raise("get_one_or_none")
        return self.one_or_none_result

    async def add(self, data):
        self.calls.append(("add", data))
        self._maybe_raise("add")
        self.added.append(data)

    async def flush(self):
        self.calls.append(("flush",))
        self._maybe_raise("flush")

    async def create_exercise(self, exercise):
        self.calls.append(("create_exercise", exercise))
        self._maybe_raise("create_exercise")
        self.exercise_entity = exercise
        return exercise

    async def create_field(self, field):
        self.calls.append(("create_field", field))
        self._maybe_raise("create_field")
        self.field = field
        return field

    async def create_variant(self, variant):
        self.calls.append(("create_variant", variant))
        self._maybe_raise("create_variant")
        self.variant = variant
        return variant

    async def create_exercise_view(self, view):
        self.calls.append(("create_exercise_view", view))
        self._maybe_raise("create_exercise_view")
        self.view = view
        return view

    async def update_exercise(self, exercise):
        self.calls.append(("update_exercise", exercise))
        self._maybe_raise("update_exercise")
        self.exercise_entity = exercise
        return exercise

    async def update_field(self, field):
        self.calls.append(("update_field", field))
        self._maybe_raise("update_field")
        self.field = field
        return field

    async def update_variant(self, variant):
        self.calls.append(("update_variant", variant))
        self._maybe_raise("update_variant")
        self.variant = variant
        return variant

    async def update_exercise_view(self, view):
        self.calls.append(("update_exercise_view", view))
        self._maybe_raise("update_exercise_view")
        self.view = view
        return view

    async def get_exercise_entity(self, exercise_id):
        self.calls.append(("get_exercise_entity", exercise_id))
        self._maybe_raise("get_exercise_entity")
        if self.exercise_entity and self.exercise_entity.id == exercise_id:
            return self.exercise_entity
        return None

    async def get_exercise_with_fields(self, exercise_id):
        self.calls.append(("get_exercise_with_fields", exercise_id))
        self._maybe_raise("get_exercise_with_fields")
        if self.exercise_entity and self.exercise_entity.id == exercise_id:
            return self.exercise_entity
        return None

    async def get_all_exercise_entities(self):
        self.calls.append(("get_all_exercise_entities",))
        self._maybe_raise("get_all_exercise_entities")
        return self.all_exercises

    async def get_completed_exercise_ids(self, user_id, exercise_ids):
        self.calls.append(("get_completed_exercise_ids", user_id, exercise_ids))
        return set(exercise_ids)

    async def is_exercise_completed(self, exercise_id, user_id):
        self.calls.append(("is_exercise_completed", exercise_id, user_id))
        self._maybe_raise("is_exercise_completed")
        return True

    async def get_field(self, field_id):
        self.calls.append(("get_field", field_id))
        return self.field

    async def get_variant(self, variant_id):
        self.calls.append(("get_variant", variant_id))
        return self.variant

    async def get_variants_by_field(self, field_id):
        self.calls.append(("get_variants_by_field", field_id))
        self._maybe_raise("get_variants_by_field")
        for field in getattr(self.exercise_entity, "field", []):
            if field.id == field_id:
                return list(getattr(field, "variants", []))
        return []

    async def get_exercise_view(self, view_id):
        self.calls.append(("get_exercise_view", view_id))
        return self.view

    async def delete_exercise(self, exercise):
        self.calls.append(("delete_exercise", exercise))
        self._maybe_raise("delete_exercise")

    async def delete_field(self, field):
        self.calls.append(("delete_field", field))
        self._maybe_raise("delete_field")

    async def delete_variant(self, variant):
        self.calls.append(("delete_variant", variant))
        self._maybe_raise("delete_variant")

    async def delete_exercise_view(self, view):
        self.calls.append(("delete_exercise_view", view))
        self._maybe_raise("delete_exercise_view")

    async def delete_fields_by_exercise(self, exercise_id):
        self.calls.append(("delete_fields_by_exercise", exercise_id))
        self._maybe_raise("delete_fields_by_exercise")

    async def delete_views_by_exercise(self, exercise_id):
        self.calls.append(("delete_views_by_exercise", exercise_id))
        self._maybe_raise("delete_views_by_exercise")

    async def delete_stale_fields_without_results(self, exercise_id, actual_field_ids):
        self.calls.append(("delete_stale_fields_without_results", exercise_id, actual_field_ids))
        self._maybe_raise("delete_stale_fields_without_results")

    async def delete_stale_variants(self, field_id, actual_variant_ids):
        self.calls.append(("delete_stale_variants", field_id, actual_variant_ids))
        self._maybe_raise("delete_stale_variants")

    async def delete_stale_views(self, exercise_id, actual_view_ids):
        self.calls.append(("delete_stale_views", exercise_id, actual_view_ids))
        self._maybe_raise("delete_stale_views")

    async def get_fields_by_exercise(self, exercise_id):
        self.calls.append(("get_fields_by_exercise", exercise_id))
        self._maybe_raise("get_fields_by_exercise")
        return list(getattr(self.exercise_entity, "field", []))

    async def get_views_by_exercise(self, exercise_id):
        self.calls.append(("get_views_by_exercise", exercise_id))
        self._maybe_raise("get_views_by_exercise")
        return [self.view] if self.view else []

    async def get_exercise_results(self, exercise_id, user_id):
        self.calls.append(("get_exercise_results", exercise_id, user_id))
        self._maybe_raise("get_exercise_results")
        return self.results

    async def get_passed_exercises_by_user(self, user_id):
        self.calls.append(("get_passed_exercises_by_user", user_id))
        self._maybe_raise("get_passed_exercises_by_user")
        return self.passed_exercises

    async def get_pulled_fields(self, exercise_id, user_id):
        self.calls.append(("get_pulled_fields", exercise_id, user_id))
        self._maybe_raise("get_pulled_fields")
        return self.pulled_fields_rows

    async def get_exercise_result_detail_rows(self, exercise_id, result_id, user_id):
        self.calls.append(("get_exercise_result_detail_rows", exercise_id, result_id, user_id))
        self._maybe_raise("get_exercise_result_detail_rows")
        return self.result_detail_rows

    async def get_exercise_result_detail(self, exercise_id, result_id, user_id):
        self.calls.append(("get_exercise_result_detail", exercise_id, result_id, user_id))
        self._maybe_raise("get_exercise_result_detail")
        for result in self.results:
            if result.id == result_id and result.exercise_structure_id == exercise_id:
                return result
        return None

    async def create_completed_exercise(self, completed, filled_fields):
        self.calls.append(("create_completed_exercise", completed, filled_fields))
        self._maybe_raise("create_completed_exercise")
        self.results = [type("Completed", (), {
            "id": completed.id,
            "exercise_structure_id": completed.exercise_structure_id,
            "user_id": completed.user_id,
            "date": completed.date,
            "filled_field": filled_fields,
        })()]

    async def get_latest_exercise_view(self, exercise_id):
        self.calls.append(("get_latest_exercise_view", exercise_id))
        self._maybe_raise("get_latest_exercise_view")
        return self.view


class FakeFieldRepository:
    def __init__(self):
        self.one_or_none_result = None
        self.added = []
        self.calls = []
        self.raise_on = {}

    def _maybe_raise(self, method):
        error = self.raise_on.get(method)
        if error:
            raise error

    async def get_one_or_none(self, **kwargs):
        self.calls.append(("get_one_or_none", kwargs))
        self._maybe_raise("get_one_or_none")
        return self.one_or_none_result

    async def add(self, data):
        self.calls.append(("add", data))
        self._maybe_raise("add")
        self.added.append(data)


class FakeOntologyRepository:
    def __init__(self):
        self.entries = []
        self.deleted = []

    async def get_filtered(self, **kwargs):
        return self.entries

    async def delete(self, **kwargs):
        self.deleted.append(kwargs)


class FakeExerciseDb:
    def __init__(self):
        self.exercise = FakeExerciseRepository()
        self.field = FakeFieldRepository()
        self.ontology_entry = FakeOntologyRepository()
        self.commit_count = 0
        self.rollback_count = 0
        self.raise_on_commit = None

    async def commit(self):
        if self.raise_on_commit:
            raise self.raise_on_commit
        self.commit_count += 1

    async def rollback(self):
        self.rollback_count += 1


@pytest.fixture
def fake_exercise_db():
    return FakeExerciseDb()


def exercise_create_schema(**overrides):
    return ExerciseCreate(**build_exercise_payload(**overrides))


def field_create_schema(**overrides):
    return FieldCreate(**build_field_payload(**overrides))


def variant_create_schema(**overrides):
    return VariantCreate(**build_variant_payload(**overrides))


def view_create_schema(**overrides):
    return ExerciseViewCreate(**build_view_payload(**overrides))


def exercise_update_schema(**overrides):
    return ExerciseUpdate(**overrides)


def field_update_schema(**overrides):
    return FieldUpdate(**overrides)


def variant_update_schema(**overrides):
    return VariantUpdate(**overrides)


def view_update_schema(**overrides):
    return ExerciseViewUpdate(**overrides)


def completed_create_schema(**overrides):
    return CompletedExerciseCreate(**build_complete_payload(**overrides))


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_service_auto_create_reads_fixture_files_and_commits(fake_exercise_db, monkeypatch):
    async def fake_seed_exercises(self):
        fake_exercise_db.exercise.calls.append(("seed_exercises",))

    monkeypatch.setattr(ExerciseService, "seed_exercises", fake_seed_exercises)

    result = await ExerciseService(fake_exercise_db).auto_create()

    assert result["status"] == "OK"
    assert fake_exercise_db.commit_count == 1
    assert ("seed_exercises",) in fake_exercise_db.exercise.calls


@pytest.mark.asyncio
async def test_service_auto_create_rolls_back_on_failure(fake_exercise_db, monkeypatch):
    async def failing_seed_exercises(self):
        raise RuntimeError("fixture failed")

    monkeypatch.setattr(ExerciseService, "seed_exercises", failing_seed_exercises)

    with pytest.raises(MyAppException):
        await ExerciseService(fake_exercise_db).auto_create()

    assert fake_exercise_db.rollback_count == 1


@pytest.mark.asyncio
async def test_service_seed_exercises_updates_existing_and_upserts_children(fake_exercise_db, monkeypatch):
    monkeypatch.setattr(
        exercise_service_module,
        "EXERCISES",
        [
            {
                "id": str(EXERCISE_ID),
                "title": "Seeded title",
                "description": "Seeded description",
                "picture_link": "/images/seeded.png",
                "time_to_read": 7,
                "questions_count": 3,
                "sort_order": 1,
                "linked_exercise_id": None,
                "fields": [
                    {
                        "id": str(FIELD_ID),
                        "title": "Seeded field",
                        "major": True,
                        "view": "default",
                        "type": "input",
                        "placeholder": "Seeded",
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

    await ExerciseService(fake_exercise_db).seed_exercises()

    assert fake_exercise_db.exercise.exercise_entity.title == "Seeded title"
    assert ("delete_stale_fields_without_results", EXERCISE_ID, {FIELD_ID}) in fake_exercise_db.exercise.calls
    assert ("delete_stale_views", EXERCISE_ID, set()) in fake_exercise_db.exercise.calls
    assert all(call[0] != "delete_fields_by_exercise" for call in fake_exercise_db.exercise.calls)
    assert fake_exercise_db.exercise.exercise_entity.field[0].title == "Seeded field"


@pytest.mark.asyncio
async def test_exercise_fixture_contains_related_chain():
    related_exercises = sorted(
        (exercise for exercise in FIXTURE_EXERCISES if exercise.get("group") == 2),
        key=lambda item: item["sort_order"],
    )

    assert len(related_exercises) == 4
    assert [exercise["sort_order"] for exercise in related_exercises] == [4, 5, 6, 7]
    assert related_exercises[0]["linked_exercise_id"] is None
    assert related_exercises[1]["linked_exercise_id"] == related_exercises[0]["id"]
    assert related_exercises[2]["linked_exercise_id"] == related_exercises[1]["id"]
    assert related_exercises[3]["linked_exercise_id"] == related_exercises[2]["id"]


@pytest.mark.asyncio
async def test_service_create_exercise_delegates_to_repository(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).create_exercise(exercise_create_schema())
    assert str(result.id)
    assert result.title == "Free writing"
    assert result.open is False
    assert fake_exercise_db.exercise.calls[0][0] == "create_exercise"


@pytest.mark.asyncio
async def test_service_update_exercise_updates_existing_exercise(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).update_exercise(
        EXERCISE_ID,
        exercise_update_schema(title="Updated title", time_to_read=10),
    )
    assert result.title == "Updated title"
    assert any(call[0] == "update_exercise" for call in fake_exercise_db.exercise.calls)

    fake_exercise_db.exercise.exercise_entity = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).update_exercise(
            EXERCISE_ID, exercise_update_schema(title="Missing")
        )


@pytest.mark.asyncio
async def test_service_create_field_requires_existing_exercise(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).create_field(EXERCISE_ID, field_create_schema())
    assert result.title == "Mood reason"
    assert result.variants == []
    fake_exercise_db.exercise.exercise_entity = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).create_field(EXERCISE_ID, field_create_schema())


@pytest.mark.asyncio
async def test_service_update_field_updates_existing_field(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).update_field(
        FIELD_ID,
        field_update_schema(title="Updated field", exercises=[EXERCISE_ID]),
    )
    assert result.title == "Updated field"
    assert result.exercises == [EXERCISE_ID]
    assert any(call[0] == "update_field" for call in fake_exercise_db.exercise.calls)

    fake_exercise_db.exercise.field = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).update_field(
            FIELD_ID, field_update_schema(title="Missing")
        )


@pytest.mark.asyncio
async def test_service_create_variant_requires_existing_field(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).create_variant(FIELD_ID, variant_create_schema())
    assert result.title == "Variant A"
    fake_exercise_db.exercise.field = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).create_variant(FIELD_ID, variant_create_schema())


@pytest.mark.asyncio
async def test_service_update_variant_updates_existing_variant(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).update_variant(
        VARIANT_ID,
        variant_update_schema(title="Updated variant"),
    )
    assert result.title == "Updated variant"
    assert any(call[0] == "update_variant" for call in fake_exercise_db.exercise.calls)

    fake_exercise_db.exercise.variant = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).update_variant(
            VARIANT_ID, variant_update_schema(title="Missing")
        )


@pytest.mark.asyncio
async def test_service_create_exercise_view_requires_existing_exercise(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).create_exercise_view(EXERCISE_ID, view_create_schema())
    assert result.view == "success"
    fake_exercise_db.exercise.exercise_entity = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).create_exercise_view(EXERCISE_ID, view_create_schema())


@pytest.mark.asyncio
async def test_service_update_exercise_view_updates_existing_view(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).update_exercise_view(
        VIEW_ID,
        view_update_schema(message="Updated message", score=99),
    )
    assert result.message == "Updated message"
    assert result.score == 99
    assert any(call[0] == "update_exercise_view" for call in fake_exercise_db.exercise.calls)

    fake_exercise_db.exercise.view = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).update_exercise_view(
            VIEW_ID, view_update_schema(message="Missing")
        )


@pytest.mark.asyncio
async def test_service_delete_exercise_requires_existing_exercise(fake_exercise_db):
    await ExerciseService(fake_exercise_db).delete_exercise(EXERCISE_ID)
    assert any(call[0] == "delete_exercise" for call in fake_exercise_db.exercise.calls)
    fake_exercise_db.exercise.exercise_entity = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).delete_exercise(EXERCISE_ID)


@pytest.mark.asyncio
async def test_service_delete_field_requires_existing_field(fake_exercise_db):
    await ExerciseService(fake_exercise_db).delete_field(FIELD_ID)
    assert any(call[0] == "delete_field" for call in fake_exercise_db.exercise.calls)
    fake_exercise_db.exercise.field = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).delete_field(FIELD_ID)


@pytest.mark.asyncio
async def test_service_delete_variant_requires_existing_variant(fake_exercise_db):
    await ExerciseService(fake_exercise_db).delete_variant(VARIANT_ID)
    assert any(call[0] == "delete_variant" for call in fake_exercise_db.exercise.calls)
    fake_exercise_db.exercise.variant = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).delete_variant(VARIANT_ID)


@pytest.mark.asyncio
async def test_service_delete_exercise_view_requires_existing_view(fake_exercise_db):
    await ExerciseService(fake_exercise_db).delete_exercise_view(VIEW_ID)
    assert any(call[0] == "delete_exercise_view" for call in fake_exercise_db.exercise.calls)
    fake_exercise_db.exercise.view = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).delete_exercise_view(VIEW_ID)


@pytest.mark.asyncio
async def test_service_get_all_exercises_delegates_user_id(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).get_all_exercises(USER_ID)
    assert result["regular_exercises"][0].title == "Free writing"
    assert result["related_exercises"] == []
    assert any(call[0] == "get_completed_exercise_ids" for call in fake_exercise_db.exercise.calls)


@pytest.mark.asyncio
async def test_service_get_passed_exercises_by_user_delegates_to_repository(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).get_passed_exercises_by_user(USER_ID)
    assert result[0].title == "Free writing"
    assert ("get_passed_exercises_by_user", USER_ID) in fake_exercise_db.exercise.calls


@pytest.mark.asyncio
async def test_service_get_exercise_by_id_returns_detail_or_not_found(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).get_exercise_by_id(EXERCISE_ID, USER_ID)
    assert result.title == "Free writing"
    assert result.open is True
    fake_exercise_db.exercise.exercise_entity = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).get_exercise_by_id(EXERCISE_ID, USER_ID)


@pytest.mark.asyncio
async def test_service_get_exercise_structure_by_id_returns_structure_or_not_found(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).get_exercise_structure_by_id(EXERCISE_ID, USER_ID)
    assert result.title == "Free writing"
    assert result.pages[0].sections[0].title == "Mood reason"
    fake_exercise_db.exercise.exercise_entity = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).get_exercise_structure_by_id(EXERCISE_ID, USER_ID)


@pytest.mark.asyncio
async def test_service_get_exercise_structure_groups_pulled_fields(fake_exercise_db):
    first_source = make_completed_orm_like(result_id=RESULT_ID)
    second_source = make_completed_orm_like(result_id=VIEW_ID)
    fake_exercise_db.exercise.pulled_fields_rows = [
        (
            make_filled_field_orm_like(
                field_id=FIELD_ID,
                text="Answer A1",
            ),
            first_source,
        ),
        (
            make_filled_field_orm_like(
                field_id=SECOND_FIELD_ID,
                text="Answer A2",
            ),
            first_source,
        ),
        (
            make_filled_field_orm_like(
                field_id=FIELD_ID,
                text="Answer B1",
            ),
            second_source,
        ),
    ]
    fake_exercise_db.exercise.pulled_fields_rows[0][0].source_group_key = "pair"
    fake_exercise_db.exercise.pulled_fields_rows[1][0].source_group_key = "pair"
    fake_exercise_db.exercise.pulled_fields_rows[2][0].source_group_key = str(FIELD_ID)

    result = await ExerciseService(fake_exercise_db).get_exercise_structure_by_id(
        EXERCISE_ID,
        USER_ID,
    )

    assert len(result.pulled_fields) == 2
    assert result.pulled_fields[0].source_group_key == "pair"
    assert len(result.pulled_fields[0].fields) == 2
    assert result.pulled_fields[1].fields[0].text == "Answer B1"


@pytest.mark.asyncio
async def test_service_get_exercise_results_delegates_to_repository(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).get_exercise_results(EXERCISE_ID, USER_ID)
    assert result.results[0].preview == "My answer"
    assert ("get_exercise_results", EXERCISE_ID, USER_ID) in fake_exercise_db.exercise.calls


@pytest.mark.asyncio
async def test_service_get_exercise_results_returns_null_preview_for_empty_result(fake_exercise_db):
    fake_exercise_db.exercise.results = [make_completed_orm_like(filled_fields=[])]

    result = await ExerciseService(fake_exercise_db).get_exercise_results(EXERCISE_ID, USER_ID)

    assert result.results[0].preview is None


@pytest.mark.asyncio
async def test_service_get_exercise_result_detail_returns_detail_or_not_found(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).get_exercise_result_detail(EXERCISE_ID, RESULT_ID, USER_ID)
    assert result.sections[0].value == "My answer"
    fake_exercise_db.exercise.results = []
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).get_exercise_result_detail(EXERCISE_ID, RESULT_ID, USER_ID)


@pytest.mark.asyncio
async def test_service_get_exercise_result_detail_returns_empty_sections_for_empty_result(fake_exercise_db):
    fake_exercise_db.exercise.results = [make_completed_orm_like(filled_fields=[])]

    result = await ExerciseService(fake_exercise_db).get_exercise_result_detail(
        EXERCISE_ID,
        RESULT_ID,
        USER_ID,
    )

    assert result.id == RESULT_ID
    assert result.sections == []


@pytest.mark.asyncio
async def test_service_complete_exercise_deletes_matching_ontology_and_commits(fake_exercise_db):
    matching_entry = type("Entry", (), {"destination_id": EXERCISE_ID})()
    other_entry = type("Entry", (), {"destination_id": VARIANT_ID})()
    fake_exercise_db.ontology_entry.entries = [matching_entry, other_entry]

    result = await ExerciseService(fake_exercise_db).complete_exercise(USER_ID, completed_create_schema())

    assert result.score == 10
    assert result.view == "success"
    assert fake_exercise_db.commit_count == 1
    assert fake_exercise_db.ontology_entry.deleted == [
        {"user_id": USER_ID, "destination_id": EXERCISE_ID}
    ]


@pytest.mark.asyncio
async def test_service_complete_exercise_keeps_pulled_group_link_and_snapshot(fake_exercise_db):
    fake_exercise_db.exercise.pulled_fields_rows = [
        (
            make_filled_field_orm_like(field_id=SECOND_FIELD_ID, text="Source answer"),
            make_completed_orm_like(result_id=SECOND_EXERCISE_ID),
        )
    ]
    fake_exercise_db.exercise.pulled_fields_rows[0][0].source_group_key = "memory"
    payload = completed_create_schema(
        filled_fields=[
            {
                "field_id": str(FIELD_ID),
                "text": "Linked answer",
                "pulled_completed_exercise_id": str(SECOND_EXERCISE_ID),
                "pulled_group_key": "memory",
            }
        ]
    )

    await ExerciseService(fake_exercise_db).complete_exercise(USER_ID, payload)

    _, _, saved_filled_fields = fake_exercise_db.exercise.calls[-2]
    assert saved_filled_fields[0].pulled_completed_exercise_id == SECOND_EXERCISE_ID
    assert saved_filled_fields[0].pulled_group_key == "memory"
    assert saved_filled_fields[0].pulled_fields_snapshot[0]["text"] == "Source answer"


@pytest.mark.asyncio
async def test_service_complete_exercise_maps_value_error_to_400(fake_exercise_db):
    fake_exercise_db.exercise.raise_on["get_exercise_with_fields"] = ValueError("Exercise not found")
    with pytest.raises(Exception) as exc_info:
        await ExerciseService(fake_exercise_db).complete_exercise(USER_ID, completed_create_schema())
    assert getattr(exc_info.value, "status_code", None) == 400


@pytest.mark.asyncio
async def test_service_complete_exercise_maps_unexpected_error_to_500(fake_exercise_db):
    fake_exercise_db.exercise.raise_on["get_exercise_with_fields"] = RuntimeError("boom")
    with pytest.raises(Exception) as exc_info:
        await ExerciseService(fake_exercise_db).complete_exercise(USER_ID, completed_create_schema())
    assert getattr(exc_info.value, "status_code", None) == 500
