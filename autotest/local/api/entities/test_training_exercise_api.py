import pytest

import src.api.training_exercise as training_api_module
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.schemas.training_exercise import ExerciseDetailResponse, ExerciseShortResponse
from autotest.factories.training_exercise import EXERCISE_ID, USER_ID

class DummyTrainingExerciseApiService:
    exercises_response = []
    detail_response = None
    structure_response = None
    completed_response = {"is_completed": False}
    raise_on_seed = None
    raise_on_get_all = None
    raise_on_detail = None
    raise_on_structure = None
    raise_on_completed = None
    raise_on_complete = None
    last_init_db = None
    last_get_all_user_id = None
    last_detail_args = None
    last_structure_args = None
    last_completed_args = None
    last_complete_args = None
    seed_called = False

    def __init__(self, db):
        self.db = db
        type(self).last_init_db = db

    @classmethod
    def reset(cls):
        cls.exercises_response = []
        cls.detail_response = None
        cls.structure_response = None
        cls.completed_response = {"is_completed": False}
        cls.raise_on_seed = None
        cls.raise_on_get_all = None
        cls.raise_on_detail = None
        cls.raise_on_structure = None
        cls.raise_on_completed = None
        cls.raise_on_complete = None
        cls.last_init_db = None
        cls.last_get_all_user_id = None
        cls.last_detail_args = None
        cls.last_structure_args = None
        cls.last_completed_args = None
        cls.last_complete_args = None
        cls.seed_called = False

    async def seed_exercises(self):
        if type(self).raise_on_seed:
            raise type(self).raise_on_seed
        type(self).seed_called = True

    async def get_all_exercises(self, user_id):
        if type(self).raise_on_get_all:
            raise type(self).raise_on_get_all
        type(self).last_get_all_user_id = user_id
        return type(self).exercises_response

    async def get_exercise_by_id(self, exercise_id, user_id):
        if type(self).raise_on_detail:
            raise type(self).raise_on_detail
        type(self).last_detail_args = (exercise_id, user_id)
        return type(self).detail_response

    async def get_exercise_structure_by_id(self, exercise_id, user_id):
        if type(self).raise_on_structure:
            raise type(self).raise_on_structure
        type(self).last_structure_args = (exercise_id, user_id)
        return type(self).structure_response

    async def is_exercise_completed_by_id(self, exercise_id, user_id):
        if type(self).raise_on_completed:
            raise type(self).raise_on_completed
        type(self).last_completed_args = (exercise_id, user_id)
        return type(self).completed_response

    async def complete_exercise(self, exercise_id, user_id):
        if type(self).raise_on_complete:
            raise type(self).raise_on_complete
        type(self).last_complete_args = (exercise_id, user_id)


@pytest.fixture
def training_api_client_factory(api_client_factory, monkeypatch):
    DummyTrainingExerciseApiService.reset()
    monkeypatch.setattr(training_api_module, "TrainingExerciseService", DummyTrainingExerciseApiService)

    def _factory(user_id=USER_ID):
        fake_db = object()

        async def override_get_db():
            yield fake_db

        def override_get_current_user_id():
            return user_id

        dependency_overrides = {
            get_db: override_get_db,
            get_current_user_id: override_get_current_user_id,
        }

        async def _client():
            async for async_client, _ in api_client_factory(
                training_api_module.router,
                dependency_overrides=dependency_overrides,
            ):
                yield async_client, fake_db

        return _client()

    return _factory


@pytest.mark.asyncio
async def test_seed_exercises_endpoint_returns_ok(training_api_client_factory):
    async for client, fake_db in training_api_client_factory():
        response = await client.post("/training-exercises/auto-create")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert DummyTrainingExerciseApiService.seed_called is True
    assert DummyTrainingExerciseApiService.last_init_db is fake_db


@pytest.mark.asyncio
async def test_seed_exercises_endpoint_returns_500_when_service_fails(training_api_client_factory):
    DummyTrainingExerciseApiService.raise_on_seed = RuntimeError("seed failed")
    async for client, _ in training_api_client_factory():
        response = await client.post("/training-exercises/auto-create")
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_all_exercises_endpoint_wraps_service_response(training_api_client_factory):
    DummyTrainingExerciseApiService.exercises_response = [
        ExerciseShortResponse(id=EXERCISE_ID, title="Detector", picture_link="/image.png", is_completed=True)
    ]
    async for client, _ in training_api_client_factory():
        response = await client.get("/training-exercises/")
    assert response.status_code == 200
    assert response.json() == {
        "exercises": [{"id": str(EXERCISE_ID), "title": "Detector", "picture_link": "/image.png", "is_completed": True}]
    }
    assert sorted(response.json().keys()) == ["exercises"]
    assert DummyTrainingExerciseApiService.last_get_all_user_id == USER_ID


@pytest.mark.asyncio
async def test_get_all_exercises_endpoint_supports_absent_user(training_api_client_factory):
    DummyTrainingExerciseApiService.exercises_response = []
    async for client, _ in training_api_client_factory(user_id=None):
        response = await client.get("/training-exercises/")
    assert response.status_code == 200
    assert response.json() == {"exercises": []}
    assert DummyTrainingExerciseApiService.last_get_all_user_id is None


@pytest.mark.asyncio
async def test_get_all_exercises_endpoint_returns_optional_picture_link_as_null(training_api_client_factory):
    DummyTrainingExerciseApiService.exercises_response = [
        ExerciseShortResponse(id=EXERCISE_ID, title="Detector", picture_link=None, is_completed=False)
    ]

    async for client, _ in training_api_client_factory():
        response = await client.get("/training-exercises/")

    assert response.status_code == 200
    assert response.json() == {
        "exercises": [
            {"id": str(EXERCISE_ID), "title": "Detector", "picture_link": None, "is_completed": False}
        ]
    }


@pytest.mark.asyncio
async def test_get_all_exercises_endpoint_returns_500_when_service_fails(training_api_client_factory):
    DummyTrainingExerciseApiService.raise_on_get_all = RuntimeError("list failed")
    async for client, _ in training_api_client_factory():
        response = await client.get("/training-exercises/")
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_exercise_endpoint_returns_detail_response(training_api_client_factory):
    DummyTrainingExerciseApiService.detail_response = ExerciseDetailResponse(
        id=EXERCISE_ID, title="Detector", picture_link="/image.png", description="Description", time_to_read=6, is_completed=False
    )
    async for client, _ in training_api_client_factory():
        response = await client.get(f"/training-exercises/{EXERCISE_ID}")
    assert response.status_code == 200
    assert response.json()["id"] == str(EXERCISE_ID)
    assert sorted(response.json().keys()) == [
        "description",
        "id",
        "is_completed",
        "picture_link",
        "time_to_read",
        "title",
    ]
    assert DummyTrainingExerciseApiService.last_detail_args == (EXERCISE_ID, USER_ID)


@pytest.mark.asyncio
async def test_get_exercise_endpoint_supports_absent_user(training_api_client_factory):
    DummyTrainingExerciseApiService.detail_response = ExerciseDetailResponse(
        id=EXERCISE_ID, title="Detector", picture_link=None, description="Description", time_to_read=6, is_completed=False
    )
    async for client, _ in training_api_client_factory(user_id=None):
        response = await client.get(f"/training-exercises/{EXERCISE_ID}")
    assert response.status_code == 200
    assert DummyTrainingExerciseApiService.last_detail_args == (EXERCISE_ID, None)


@pytest.mark.asyncio
async def test_get_exercise_endpoint_returns_optional_picture_link_as_null(training_api_client_factory):
    DummyTrainingExerciseApiService.detail_response = ExerciseDetailResponse(
        id=EXERCISE_ID,
        title="Detector",
        picture_link=None,
        description="Description",
        time_to_read=6,
        is_completed=False,
    )

    async for client, _ in training_api_client_factory():
        response = await client.get(f"/training-exercises/{EXERCISE_ID}")

    assert response.status_code == 200
    assert response.json()["picture_link"] is None


@pytest.mark.asyncio
async def test_get_exercise_endpoint_returns_422_for_invalid_uuid(training_api_client_factory):
    async for client, _ in training_api_client_factory():
        response = await client.get("/training-exercises/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_exercise_endpoint_returns_404_when_service_reports_missing_entity(training_api_client_factory):
    DummyTrainingExerciseApiService.raise_on_detail = ValueError("not found")
    async for client, _ in training_api_client_factory():
        response = await client.get(f"/training-exercises/{EXERCISE_ID}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_exercise_endpoint_returns_500_when_service_raises_unexpected_error(training_api_client_factory):
    DummyTrainingExerciseApiService.raise_on_detail = RuntimeError("detail failed")

    async for client, _ in training_api_client_factory():
        response = await client.get(f"/training-exercises/{EXERCISE_ID}")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_exercise_structure_endpoint_returns_structure(training_api_client_factory):
    DummyTrainingExerciseApiService.structure_response = {
        "id": str(EXERCISE_ID),
        "questions": [{"text": "Q1", "variants": [{"title": "A", "correct": True}]}],
    }
    async for client, _ in training_api_client_factory():
        response = await client.get(f"/training-exercises/{EXERCISE_ID}/structure")
    assert response.status_code == 200
    assert response.json()["id"] == str(EXERCISE_ID)
    assert response.json()["questions"][0]["text"] == "Q1"
    assert DummyTrainingExerciseApiService.last_structure_args == (EXERCISE_ID, USER_ID)


@pytest.mark.asyncio
async def test_get_exercise_structure_endpoint_supports_absent_user(training_api_client_factory):
    DummyTrainingExerciseApiService.structure_response = {"id": str(EXERCISE_ID), "questions": []}
    async for client, _ in training_api_client_factory(user_id=None):
        response = await client.get(f"/training-exercises/{EXERCISE_ID}/structure")
    assert response.status_code == 200
    assert DummyTrainingExerciseApiService.last_structure_args == (EXERCISE_ID, None)


@pytest.mark.asyncio
async def test_get_exercise_structure_endpoint_returns_422_for_invalid_uuid(training_api_client_factory):
    async for client, _ in training_api_client_factory():
        response = await client.get("/training-exercises/not-a-uuid/structure")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_exercise_structure_endpoint_returns_404_when_service_reports_missing_entity(training_api_client_factory):
    DummyTrainingExerciseApiService.raise_on_structure = ValueError("structure failed")
    async for client, _ in training_api_client_factory():
        response = await client.get(f"/training-exercises/{EXERCISE_ID}/structure")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_exercise_structure_endpoint_returns_500_when_service_raises_unexpected_error(training_api_client_factory):
    DummyTrainingExerciseApiService.raise_on_structure = RuntimeError("structure crashed")

    async for client, _ in training_api_client_factory():
        response = await client.get(f"/training-exercises/{EXERCISE_ID}/structure")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_is_exercise_completed_endpoint_returns_service_payload(training_api_client_factory):
    DummyTrainingExerciseApiService.completed_response = {"is_completed": True}
    async for client, _ in training_api_client_factory():
        response = await client.get(f"/training-exercises/{EXERCISE_ID}/completed")
    assert response.status_code == 200
    assert response.json() == {"is_completed": True}
    assert DummyTrainingExerciseApiService.last_completed_args == (EXERCISE_ID, USER_ID)


@pytest.mark.asyncio
async def test_is_exercise_completed_endpoint_supports_absent_user(training_api_client_factory):
    DummyTrainingExerciseApiService.completed_response = {"is_completed": False}
    async for client, _ in training_api_client_factory(user_id=None):
        response = await client.get(f"/training-exercises/{EXERCISE_ID}/completed")
    assert response.status_code == 200
    assert response.json() == {"is_completed": False}
    assert DummyTrainingExerciseApiService.last_completed_args == (EXERCISE_ID, None)


@pytest.mark.asyncio
async def test_is_exercise_completed_endpoint_returns_only_expected_key(training_api_client_factory):
    DummyTrainingExerciseApiService.completed_response = {"is_completed": False}

    async for client, _ in training_api_client_factory():
        response = await client.get(f"/training-exercises/{EXERCISE_ID}/completed")

    assert response.status_code == 200
    assert sorted(response.json().keys()) == ["is_completed"]


@pytest.mark.asyncio
async def test_is_exercise_completed_endpoint_returns_422_for_invalid_uuid(training_api_client_factory):
    async for client, _ in training_api_client_factory():
        response = await client.get("/training-exercises/not-a-uuid/completed")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_is_exercise_completed_endpoint_returns_500_when_service_fails(training_api_client_factory):
    DummyTrainingExerciseApiService.raise_on_completed = RuntimeError("completed failed")
    async for client, _ in training_api_client_factory():
        response = await client.get(f"/training-exercises/{EXERCISE_ID}/completed")
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_complete_exercise_endpoint_returns_ok(training_api_client_factory):
    async for client, _ in training_api_client_factory():
        response = await client.post(f"/training-exercises/{EXERCISE_ID}/complete")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert DummyTrainingExerciseApiService.last_complete_args == (EXERCISE_ID, USER_ID)


@pytest.mark.asyncio
async def test_complete_exercise_endpoint_supports_absent_user(training_api_client_factory):
    async for client, _ in training_api_client_factory(user_id=None):
        response = await client.post(f"/training-exercises/{EXERCISE_ID}/complete")
    assert response.status_code == 200
    assert DummyTrainingExerciseApiService.last_complete_args == (EXERCISE_ID, None)


@pytest.mark.asyncio
async def test_complete_exercise_endpoint_returns_only_status_key(training_api_client_factory):
    async for client, _ in training_api_client_factory():
        response = await client.post(f"/training-exercises/{EXERCISE_ID}/complete")

    assert response.status_code == 200
    assert sorted(response.json().keys()) == ["status"]


@pytest.mark.asyncio
async def test_complete_exercise_endpoint_returns_422_for_invalid_uuid(training_api_client_factory):
    async for client, _ in training_api_client_factory():
        response = await client.post("/training-exercises/not-a-uuid/complete")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_complete_exercise_endpoint_returns_500_when_service_fails(training_api_client_factory):
    DummyTrainingExerciseApiService.raise_on_complete = RuntimeError("complete failed")
    async for client, _ in training_api_client_factory():
        response = await client.post(f"/training-exercises/{EXERCISE_ID}/complete")
    assert response.status_code == 500
