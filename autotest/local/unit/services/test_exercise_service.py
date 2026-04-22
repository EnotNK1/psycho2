import pytest

import src.services.exercise as exercise_service_module
from autotest.factories.exercise import (
    EXERCISE_ID,
    FIELD_ID,
    RESULT_ID,
    USER_ID,
    VARIANT_ID,
    VIEW_ID,
    build_complete_payload,
    build_completed_response,
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
)
from src.exceptions import MyAppException, ObjectAlreadyExistsException, ObjectNotFoundHTTPException
from src.schemas.exercise import (
    CompletedExerciseCreate,
    ExerciseCreate,
    ExerciseViewCreate,
    FieldCreate,
    VariantCreate,
)
from src.services.exercise import ExerciseService


class FakeExerciseRepository:
    def __init__(self):
        self.exists = True
        self.field = object()
        self.variant = object()
        self.view = object()
        self.one_or_none_result = None
        self.added = []
        self.created_exercise = build_exercise_response()
        self.created_field = build_field_response()
        self.created_variant = build_variant_response()
        self.created_view = build_view_response()
        self.all_exercises = [build_exercise_response()]
        self.detail = build_exercise_detail_response()
        self.structure = build_structure_response()
        self.results = build_results_response()
        self.result_detail = build_result_detail_response()
        self.completed = build_completed_response()
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

    async def create_exercise(self, exercise_data):
        self.calls.append(("create_exercise", exercise_data))
        self._maybe_raise("create_exercise")
        return self.created_exercise

    async def create_field(self, exercise_id, field_data):
        self.calls.append(("create_field", exercise_id, field_data))
        self._maybe_raise("create_field")
        return self.created_field

    async def create_variant(self, field_id, variant_data):
        self.calls.append(("create_variant", field_id, variant_data))
        self._maybe_raise("create_variant")
        return self.created_variant

    async def create_exercise_view(self, exercise_id, view_data):
        self.calls.append(("create_exercise_view", exercise_id, view_data))
        self._maybe_raise("create_exercise_view")
        return self.created_view

    async def exercise_exists(self, exercise_id):
        self.calls.append(("exercise_exists", exercise_id))
        return self.exists

    async def get_field(self, field_id):
        self.calls.append(("get_field", field_id))
        return self.field

    async def get_variant(self, variant_id):
        self.calls.append(("get_variant", variant_id))
        return self.variant

    async def get_exercise_view(self, view_id):
        self.calls.append(("get_exercise_view", view_id))
        return self.view

    async def delete_exercise(self, exercise_id):
        self.calls.append(("delete_exercise", exercise_id))
        self._maybe_raise("delete_exercise")

    async def delete_field(self, field_id):
        self.calls.append(("delete_field", field_id))
        self._maybe_raise("delete_field")

    async def delete_variant(self, variant_id):
        self.calls.append(("delete_variant", variant_id))
        self._maybe_raise("delete_variant")

    async def delete_exercise_view(self, view_id):
        self.calls.append(("delete_exercise_view", view_id))
        self._maybe_raise("delete_exercise_view")

    async def get_all_exercises(self, user_id):
        self.calls.append(("get_all_exercises", user_id))
        self._maybe_raise("get_all_exercises")
        return self.all_exercises

    async def get_exercise(self, exercise_id, user_id):
        self.calls.append(("get_exercise", exercise_id, user_id))
        self._maybe_raise("get_exercise")
        return self.detail

    async def get_exercise_strucuture(self, exercise_id, user_id):
        self.calls.append(("get_exercise_strucuture", exercise_id, user_id))
        self._maybe_raise("get_exercise_strucuture")
        return self.structure

    async def get_exercise_results(self, exercise_id, user_id):
        self.calls.append(("get_exercise_results", exercise_id, user_id))
        self._maybe_raise("get_exercise_results")
        return self.results

    async def get_exercise_result_detail(self, exercise_id, result_id, user_id):
        self.calls.append(("get_exercise_result_detail", exercise_id, result_id, user_id))
        self._maybe_raise("get_exercise_result_detail")
        return self.result_detail

    async def complete_exercise(self, user_id, completed_data):
        self.calls.append(("complete_exercise", user_id, completed_data))
        self._maybe_raise("complete_exercise")
        return self.completed


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


def completed_create_schema(**overrides):
    return CompletedExerciseCreate(**build_complete_payload(**overrides))


@pytest.mark.asyncio
async def test_service_add_exercises_adds_only_missing_exercises(fake_exercise_db):
    data = [dict(build_exercise_payload(), id=str(EXERCISE_ID))]
    await ExerciseService(fake_exercise_db).add_exercises(data)
    assert len(fake_exercise_db.exercise.added) == 1
    assert fake_exercise_db.rollback_count == 0


@pytest.mark.asyncio
async def test_service_add_exercises_skips_existing_exercise(fake_exercise_db):
    fake_exercise_db.exercise.one_or_none_result = object()
    data = [dict(build_exercise_payload(), id=str(EXERCISE_ID))]
    await ExerciseService(fake_exercise_db).add_exercises(data)
    assert fake_exercise_db.exercise.added == []


@pytest.mark.asyncio
async def test_service_add_exercises_skips_already_exists_error(fake_exercise_db):
    fake_exercise_db.exercise.raise_on["add"] = ObjectAlreadyExistsException()
    data = [dict(build_exercise_payload(), id=str(EXERCISE_ID))]
    await ExerciseService(fake_exercise_db).add_exercises(data)
    assert fake_exercise_db.rollback_count == 0


@pytest.mark.asyncio
async def test_service_add_exercises_rolls_back_on_unexpected_error(fake_exercise_db):
    fake_exercise_db.exercise.raise_on["add"] = RuntimeError("boom")
    data = [dict(build_exercise_payload(), id=str(EXERCISE_ID))]
    with pytest.raises(MyAppException):
        await ExerciseService(fake_exercise_db).add_exercises(data)
    assert fake_exercise_db.rollback_count == 1


@pytest.mark.asyncio
async def test_service_add_fields_adds_field_when_parent_exercise_exists(fake_exercise_db):
    data = [dict(build_field_payload(), id=str(FIELD_ID), exercise_structure_id=str(EXERCISE_ID))]
    fake_exercise_db.exercise.one_or_none_result = object()
    await ExerciseService(fake_exercise_db).add_fields(data)
    assert len(fake_exercise_db.field.added) == 1


@pytest.mark.asyncio
async def test_service_add_fields_rejects_field_without_parent_reference(fake_exercise_db):
    data = [dict(build_field_payload(), id=str(FIELD_ID), exercise_structure_id=None)]
    with pytest.raises(Exception):
        await ExerciseService(fake_exercise_db).add_fields(data)
    assert fake_exercise_db.field.added == []


@pytest.mark.asyncio
async def test_service_add_fields_skips_missing_parent_exercise(fake_exercise_db):
    data = [dict(build_field_payload(), id=str(FIELD_ID), exercise_structure_id=str(EXERCISE_ID))]
    await ExerciseService(fake_exercise_db).add_fields(data)
    assert fake_exercise_db.field.added == []


@pytest.mark.asyncio
async def test_service_add_fields_rolls_back_on_unexpected_error(fake_exercise_db):
    data = [dict(build_field_payload(), id=str(FIELD_ID), exercise_structure_id=str(EXERCISE_ID))]
    fake_exercise_db.exercise.one_or_none_result = object()
    fake_exercise_db.field.raise_on["add"] = RuntimeError("boom")
    with pytest.raises(MyAppException):
        await ExerciseService(fake_exercise_db).add_fields(data)
    assert fake_exercise_db.rollback_count == 1


@pytest.mark.asyncio
async def test_service_auto_create_reads_fixture_files_and_commits(fake_exercise_db, monkeypatch):
    async def fake_add_exercises(self, exercises_data):
        fake_exercise_db.exercise.calls.append(("auto_add_exercises", exercises_data))

    async def fake_add_fields(self, fields_data):
        fake_exercise_db.exercise.calls.append(("auto_add_fields", fields_data))

    monkeypatch.setattr(ExerciseService, "add_exercises", fake_add_exercises)
    monkeypatch.setattr(ExerciseService, "add_fields", fake_add_fields)
    monkeypatch.setattr(exercise_service_module.json, "load", lambda file: [{"id": str(EXERCISE_ID)}])

    result = await ExerciseService(fake_exercise_db).auto_create()

    assert result["status"] == "OK"
    assert fake_exercise_db.commit_count == 1
    assert ("auto_add_exercises", [{"id": str(EXERCISE_ID)}]) in fake_exercise_db.exercise.calls
    assert ("auto_add_fields", [{"id": str(EXERCISE_ID)}]) in fake_exercise_db.exercise.calls


@pytest.mark.asyncio
async def test_service_auto_create_rolls_back_on_failure(fake_exercise_db, monkeypatch):
    async def failing_add_exercises(self, exercises_data):
        raise RuntimeError("fixture failed")

    monkeypatch.setattr(ExerciseService, "add_exercises", failing_add_exercises)
    monkeypatch.setattr(exercise_service_module.json, "load", lambda file: [])

    with pytest.raises(MyAppException):
        await ExerciseService(fake_exercise_db).auto_create()

    assert fake_exercise_db.rollback_count == 1


@pytest.mark.asyncio
async def test_service_create_exercise_delegates_to_repository(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).create_exercise(exercise_create_schema())
    assert result == build_exercise_response()
    assert fake_exercise_db.exercise.calls[0][0] == "create_exercise"


@pytest.mark.asyncio
async def test_service_create_field_requires_existing_exercise(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).create_field(EXERCISE_ID, field_create_schema())
    assert result == build_field_response()
    fake_exercise_db.exercise.exists = False
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).create_field(EXERCISE_ID, field_create_schema())


@pytest.mark.asyncio
async def test_service_create_variant_requires_existing_field(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).create_variant(FIELD_ID, variant_create_schema())
    assert result == build_variant_response()
    fake_exercise_db.exercise.field = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).create_variant(FIELD_ID, variant_create_schema())


@pytest.mark.asyncio
async def test_service_create_exercise_view_requires_existing_exercise(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).create_exercise_view(EXERCISE_ID, view_create_schema())
    assert result == build_view_response()
    fake_exercise_db.exercise.exists = False
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).create_exercise_view(EXERCISE_ID, view_create_schema())


@pytest.mark.asyncio
async def test_service_delete_exercise_requires_existing_exercise(fake_exercise_db):
    await ExerciseService(fake_exercise_db).delete_exercise(EXERCISE_ID)
    assert ("delete_exercise", EXERCISE_ID) in fake_exercise_db.exercise.calls
    fake_exercise_db.exercise.exists = False
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).delete_exercise(EXERCISE_ID)


@pytest.mark.asyncio
async def test_service_delete_field_requires_existing_field(fake_exercise_db):
    await ExerciseService(fake_exercise_db).delete_field(FIELD_ID)
    assert ("delete_field", FIELD_ID) in fake_exercise_db.exercise.calls
    fake_exercise_db.exercise.field = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).delete_field(FIELD_ID)


@pytest.mark.asyncio
async def test_service_delete_variant_requires_existing_variant(fake_exercise_db):
    await ExerciseService(fake_exercise_db).delete_variant(VARIANT_ID)
    assert ("delete_variant", VARIANT_ID) in fake_exercise_db.exercise.calls
    fake_exercise_db.exercise.variant = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).delete_variant(VARIANT_ID)


@pytest.mark.asyncio
async def test_service_delete_exercise_view_requires_existing_view(fake_exercise_db):
    await ExerciseService(fake_exercise_db).delete_exercise_view(VIEW_ID)
    assert ("delete_exercise_view", VIEW_ID) in fake_exercise_db.exercise.calls
    fake_exercise_db.exercise.view = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).delete_exercise_view(VIEW_ID)


@pytest.mark.asyncio
async def test_service_get_all_exercises_delegates_user_id(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).get_all_exercises(USER_ID)
    assert result == [build_exercise_response()]
    assert ("get_all_exercises", USER_ID) in fake_exercise_db.exercise.calls


@pytest.mark.asyncio
async def test_service_get_exercise_by_id_returns_detail_or_not_found(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).get_exercise_by_id(EXERCISE_ID, USER_ID)
    assert result == build_exercise_detail_response()
    fake_exercise_db.exercise.detail = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).get_exercise_by_id(EXERCISE_ID, USER_ID)


@pytest.mark.asyncio
async def test_service_get_exercise_structure_by_id_returns_structure_or_not_found(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).get_exercise_structure_by_id(EXERCISE_ID, USER_ID)
    assert result == build_structure_response()
    fake_exercise_db.exercise.structure = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).get_exercise_structure_by_id(EXERCISE_ID, USER_ID)


@pytest.mark.asyncio
async def test_service_get_exercise_results_delegates_to_repository(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).get_exercise_results(EXERCISE_ID, USER_ID)
    assert result == build_results_response()
    assert ("get_exercise_results", EXERCISE_ID, USER_ID) in fake_exercise_db.exercise.calls


@pytest.mark.asyncio
async def test_service_get_exercise_result_detail_returns_detail_or_not_found(fake_exercise_db):
    result = await ExerciseService(fake_exercise_db).get_exercise_result_detail(EXERCISE_ID, RESULT_ID, USER_ID)
    assert result == build_result_detail_response()
    fake_exercise_db.exercise.result_detail = None
    with pytest.raises(ObjectNotFoundHTTPException):
        await ExerciseService(fake_exercise_db).get_exercise_result_detail(EXERCISE_ID, RESULT_ID, USER_ID)


@pytest.mark.asyncio
async def test_service_complete_exercise_deletes_matching_ontology_and_commits(fake_exercise_db):
    matching_entry = type("Entry", (), {"destination_id": EXERCISE_ID})()
    other_entry = type("Entry", (), {"destination_id": VARIANT_ID})()
    fake_exercise_db.ontology_entry.entries = [matching_entry, other_entry]

    result = await ExerciseService(fake_exercise_db).complete_exercise(USER_ID, completed_create_schema())

    assert result == build_completed_response()
    assert fake_exercise_db.commit_count == 1
    assert fake_exercise_db.ontology_entry.deleted == [
        {"user_id": USER_ID, "destination_id": EXERCISE_ID}
    ]


@pytest.mark.asyncio
async def test_service_complete_exercise_maps_value_error_to_400(fake_exercise_db):
    fake_exercise_db.exercise.raise_on["complete_exercise"] = ValueError("Exercise not found")
    with pytest.raises(Exception) as exc_info:
        await ExerciseService(fake_exercise_db).complete_exercise(USER_ID, completed_create_schema())
    assert getattr(exc_info.value, "status_code", None) == 400


@pytest.mark.asyncio
async def test_service_complete_exercise_maps_unexpected_error_to_500(fake_exercise_db):
    fake_exercise_db.exercise.raise_on["complete_exercise"] = RuntimeError("boom")
    with pytest.raises(Exception) as exc_info:
        await ExerciseService(fake_exercise_db).complete_exercise(USER_ID, completed_create_schema())
    assert getattr(exc_info.value, "status_code", None) == 500
