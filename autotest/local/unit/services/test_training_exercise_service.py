import pytest

import src.services.training_exercise as training_service_module
from autotest4.factories.training_exercise import (
    EXERCISE_ID,
    SECOND_EXERCISE_ID,
    USER_ID,
    make_exercise,
    sample_seed_fixture,
)
from src.models.training_exercises import (
    TrainingCompletedExerciseOrm,
    TrainingExerciseOrm,
    TrainingQuestionOrm,
    TrainingVariantOrm,
)
from src.services.training_exercise import TrainingExerciseService


class FakeTrainingExerciseRepository:
    def __init__(self):
        self.all_items = []
        self.completed_map = set()
        self.exercise_by_id = None
        self.structure_by_id = None
        self.completed_bool = False
        self.existing_seed_item = None
        self.deleted_question_ids = []
        self.added = []
        self.flush_count = 0
        self.get_all_calls = 0
        self.get_completed_map_calls = []
        self.get_by_id_calls = []
        self.is_completed_calls = []
        self.get_with_structure_calls = []
        self.flush_should_raise = None

    async def get_all(self):
        self.get_all_calls += 1
        return self.all_items

    async def get_completed_map(self, user_id):
        self.get_completed_map_calls.append(user_id)
        return self.completed_map

    async def get_by_id(self, exercise_id):
        self.get_by_id_calls.append(exercise_id)
        if self.exercise_by_id is not None:
            return self.exercise_by_id if self.exercise_by_id.id == exercise_id else None
        if self.existing_seed_item is not None and self.existing_seed_item.id == exercise_id:
            return self.existing_seed_item
        return None

    async def is_completed(self, exercise_id, user_id):
        self.is_completed_calls.append((exercise_id, user_id))
        return self.completed_bool

    async def get_with_structure(self, exercise_id):
        self.get_with_structure_calls.append(exercise_id)
        return self.structure_by_id

    async def add(self, instance):
        self.added.append(instance)

    async def delete_questions(self, exercise_id):
        self.deleted_question_ids.append(exercise_id)

    async def flush(self):
        if self.flush_should_raise:
            raise self.flush_should_raise
        self.flush_count += 1


class FakeTrainingCompletedExerciseRepository:
    def __init__(self):
        self.one_or_none_result = None
        self.calls = []
        self.raise_on_get = None

    async def get_one_or_none(self, **filter_by):
        self.calls.append(filter_by)
        if self.raise_on_get:
            raise self.raise_on_get
        return self.one_or_none_result


class FakeTrainingDb:
    def __init__(self):
        self.training_exercise = FakeTrainingExerciseRepository()
        self.training_completed_exercise = FakeTrainingCompletedExerciseRepository()
        self.commit_count = 0
        self.commit_should_raise = None

    async def commit(self):
        if self.commit_should_raise:
            raise self.commit_should_raise
        self.commit_count += 1


@pytest.fixture
def fake_training_db():
    return FakeTrainingDb()


@pytest.mark.asyncio
async def test_service_get_all_exercises_marks_completed(fake_training_db):
    fake_training_db.training_exercise.all_items = [make_exercise(EXERCISE_ID, "First"), make_exercise(SECOND_EXERCISE_ID, "Second")]
    fake_training_db.training_exercise.completed_map = {EXERCISE_ID}
    result = await TrainingExerciseService(fake_training_db).get_all_exercises(USER_ID)
    assert [item.title for item in result] == ["First", "Second"]
    assert [item.is_completed for item in result] == [True, False]
    assert fake_training_db.training_exercise.get_completed_map_calls == [USER_ID]


@pytest.mark.asyncio
async def test_service_get_all_exercises_without_user_marks_all_not_completed(fake_training_db):
    fake_training_db.training_exercise.all_items = [make_exercise()]
    result = await TrainingExerciseService(fake_training_db).get_all_exercises(None)
    assert len(result) == 1
    assert result[0].is_completed is False
    assert fake_training_db.training_exercise.get_completed_map_calls == []


@pytest.mark.asyncio
async def test_service_get_all_exercises_returns_empty_list_for_empty_repository(fake_training_db):
    result = await TrainingExerciseService(fake_training_db).get_all_exercises(USER_ID)
    assert result == []


@pytest.mark.asyncio
async def test_service_get_exercise_by_id_returns_detail_with_completion_state(fake_training_db):
    fake_training_db.training_exercise.exercise_by_id = make_exercise()
    fake_training_db.training_exercise.completed_bool = True
    result = await TrainingExerciseService(fake_training_db).get_exercise_by_id(EXERCISE_ID, USER_ID)
    assert result.id == EXERCISE_ID
    assert result.is_completed is True
    assert fake_training_db.training_exercise.is_completed_calls == [(EXERCISE_ID, USER_ID)]


@pytest.mark.asyncio
async def test_service_get_exercise_by_id_without_user_skips_completion_check(fake_training_db):
    fake_training_db.training_exercise.exercise_by_id = make_exercise()
    result = await TrainingExerciseService(fake_training_db).get_exercise_by_id(EXERCISE_ID, None)
    assert result.is_completed is False
    assert fake_training_db.training_exercise.is_completed_calls == []


@pytest.mark.asyncio
async def test_service_get_exercise_by_id_raises_for_missing_exercise(fake_training_db):
    with pytest.raises(ValueError, match="Exercise not found"):
        await TrainingExerciseService(fake_training_db).get_exercise_by_id(EXERCISE_ID, USER_ID)


@pytest.mark.asyncio
async def test_service_get_exercise_structure_by_id_returns_structure(fake_training_db):
    fake_training_db.training_exercise.structure_by_id = {"id": str(EXERCISE_ID), "questions": []}
    result = await TrainingExerciseService(fake_training_db).get_exercise_structure_by_id(EXERCISE_ID, USER_ID)
    assert result == {"id": str(EXERCISE_ID), "questions": []}
    assert fake_training_db.training_exercise.get_with_structure_calls == [EXERCISE_ID]


@pytest.mark.asyncio
async def test_service_get_exercise_structure_by_id_returns_full_nested_structure(fake_training_db):
    fake_training_db.training_exercise.structure_by_id = {"id": str(EXERCISE_ID), "questions": [{"id": "q1", "text": "Question 1", "variants": [{"title": "A"}, {"title": "B"}]}]}
    result = await TrainingExerciseService(fake_training_db).get_exercise_structure_by_id(EXERCISE_ID, USER_ID)
    assert result["questions"][0]["variants"][1]["title"] == "B"


@pytest.mark.asyncio
async def test_service_get_exercise_structure_by_id_raises_for_missing_exercise(fake_training_db):
    with pytest.raises(ValueError, match="Exercise not found"):
        await TrainingExerciseService(fake_training_db).get_exercise_structure_by_id(EXERCISE_ID, USER_ID)


@pytest.mark.asyncio
async def test_service_is_exercise_completed_by_id_returns_false_without_user(fake_training_db):
    result = await TrainingExerciseService(fake_training_db).is_exercise_completed_by_id(EXERCISE_ID, None)
    assert result == {"is_completed": False}
    assert fake_training_db.training_exercise.is_completed_calls == []


@pytest.mark.asyncio
async def test_service_is_exercise_completed_by_id_delegates_to_repository(fake_training_db):
    fake_training_db.training_exercise.completed_bool = True
    result = await TrainingExerciseService(fake_training_db).is_exercise_completed_by_id(EXERCISE_ID, USER_ID)
    assert result == {"is_completed": True}
    assert fake_training_db.training_exercise.is_completed_calls == [(EXERCISE_ID, USER_ID)]


@pytest.mark.asyncio
async def test_service_complete_exercise_creates_completion_record(fake_training_db):
    await TrainingExerciseService(fake_training_db).complete_exercise(EXERCISE_ID, USER_ID)
    created = fake_training_db.training_exercise.added[0]
    assert isinstance(created, TrainingCompletedExerciseOrm)
    assert created.training_exercise_id == EXERCISE_ID
    assert created.user_id == USER_ID
    assert fake_training_db.commit_count == 1


@pytest.mark.asyncio
async def test_service_complete_exercise_skips_when_already_completed(fake_training_db):
    fake_training_db.training_completed_exercise.one_or_none_result = object()
    await TrainingExerciseService(fake_training_db).complete_exercise(EXERCISE_ID, USER_ID)
    assert fake_training_db.training_exercise.added == []
    assert fake_training_db.commit_count == 0


@pytest.mark.asyncio
async def test_service_complete_exercise_without_user_still_persists_none_user_record(fake_training_db):
    await TrainingExerciseService(fake_training_db).complete_exercise(EXERCISE_ID, None)

    created = fake_training_db.training_exercise.added[0]
    assert isinstance(created, TrainingCompletedExerciseOrm)
    assert created.user_id is None
    assert fake_training_db.commit_count == 1


@pytest.mark.asyncio
async def test_service_complete_exercise_propagates_repository_error(fake_training_db):
    fake_training_db.training_completed_exercise.raise_on_get = RuntimeError("repo failed")
    with pytest.raises(RuntimeError, match="repo failed"):
        await TrainingExerciseService(fake_training_db).complete_exercise(EXERCISE_ID, USER_ID)


@pytest.mark.asyncio
async def test_service_complete_exercise_propagates_commit_error(fake_training_db):
    fake_training_db.commit_should_raise = RuntimeError("commit failed")
    with pytest.raises(RuntimeError, match="commit failed"):
        await TrainingExerciseService(fake_training_db).complete_exercise(EXERCISE_ID, USER_ID)


@pytest.mark.asyncio
async def test_service_seed_exercises_creates_records_from_fixture(fake_training_db, monkeypatch):
    monkeypatch.setattr(training_service_module, "TRAINING_EXERCISES", sample_seed_fixture())
    await TrainingExerciseService(fake_training_db).seed_exercises()
    added = fake_training_db.training_exercise.added
    assert len(added) == 4
    assert isinstance(added[0], TrainingExerciseOrm)
    assert isinstance(added[1], TrainingQuestionOrm)
    assert isinstance(added[2], TrainingVariantOrm)
    assert isinstance(added[3], TrainingVariantOrm)
    assert fake_training_db.training_exercise.flush_count == 2


@pytest.mark.asyncio
async def test_service_seed_exercises_sets_expected_fields_on_created_records(fake_training_db, monkeypatch):
    monkeypatch.setattr(training_service_module, "TRAINING_EXERCISES", sample_seed_fixture())
    await TrainingExerciseService(fake_training_db).seed_exercises()
    exercise, question, first_variant, second_variant = fake_training_db.training_exercise.added
    assert exercise.id == EXERCISE_ID
    assert question.text == "Question 1"
    assert first_variant.title == "A"
    assert second_variant.title == "B"


@pytest.mark.asyncio
async def test_service_seed_exercises_updates_existing_record_and_deletes_old_questions(fake_training_db, monkeypatch):
    existing = make_exercise()
    monkeypatch.setattr(training_service_module, "TRAINING_EXERCISES", sample_seed_fixture())
    fake_training_db.training_exercise.existing_seed_item = existing
    await TrainingExerciseService(fake_training_db).seed_exercises()
    assert fake_training_db.training_exercise.deleted_question_ids == [EXERCISE_ID]
    assert existing.title == "Detector"


@pytest.mark.asyncio
async def test_service_seed_exercises_does_not_readd_existing_exercise(fake_training_db, monkeypatch):
    existing = make_exercise()
    monkeypatch.setattr(training_service_module, "TRAINING_EXERCISES", sample_seed_fixture())
    fake_training_db.training_exercise.existing_seed_item = existing
    await TrainingExerciseService(fake_training_db).seed_exercises()
    assert all(not isinstance(item, TrainingExerciseOrm) for item in fake_training_db.training_exercise.added)


@pytest.mark.asyncio
async def test_service_seed_exercises_commits_even_when_fixture_is_empty(fake_training_db, monkeypatch):
    monkeypatch.setattr(training_service_module, "TRAINING_EXERCISES", [])
    await TrainingExerciseService(fake_training_db).seed_exercises()
    assert fake_training_db.commit_count == 1


@pytest.mark.asyncio
async def test_service_seed_exercises_supports_multiple_questions_and_variants(fake_training_db, monkeypatch):
    fixture = sample_seed_fixture()
    fixture[0]["questions"].append({"text": "Question 2", "variants": [{"title": "C", "correct": False, "explanation": "maybe"}]})
    monkeypatch.setattr(training_service_module, "TRAINING_EXERCISES", fixture)
    await TrainingExerciseService(fake_training_db).seed_exercises()
    assert len(fake_training_db.training_exercise.added) == 6


@pytest.mark.asyncio
async def test_service_seed_exercises_propagates_flush_error(fake_training_db, monkeypatch):
    monkeypatch.setattr(training_service_module, "TRAINING_EXERCISES", sample_seed_fixture())
    fake_training_db.training_exercise.flush_should_raise = RuntimeError("flush failed")
    with pytest.raises(RuntimeError, match="flush failed"):
        await TrainingExerciseService(fake_training_db).seed_exercises()


@pytest.mark.asyncio
async def test_service_seed_exercises_propagates_commit_error(fake_training_db, monkeypatch):
    monkeypatch.setattr(training_service_module, "TRAINING_EXERCISES", sample_seed_fixture())
    fake_training_db.commit_should_raise = RuntimeError("commit failed")
    with pytest.raises(RuntimeError, match="commit failed"):
        await TrainingExerciseService(fake_training_db).seed_exercises()
