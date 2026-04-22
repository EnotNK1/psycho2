import pytest

import src.api.training_exercise as training_api_module
from autotest.factories.training_exercise import EXERCISE_ID, USER_ID
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id


class DummyTrainingExerciseSmokeService:
    def __init__(self, db):
        self.db = db

    async def seed_exercises(self):
        return None

    async def get_all_exercises(self, user_id):
        return [
            {
                "id": EXERCISE_ID,
                "title": "Detector",
                "picture_link": "/image.png",
                "is_completed": False,
            }
        ]

    async def get_exercise_by_id(self, exercise_id, user_id):
        return {
            "id": exercise_id,
            "title": "Detector",
            "picture_link": "/image.png",
            "description": "Description",
            "time_to_read": 5,
            "is_completed": False,
        }

    async def get_exercise_structure_by_id(self, exercise_id, user_id):
        return {"id": str(exercise_id), "questions": []}

    async def is_exercise_completed_by_id(self, exercise_id, user_id):
        return {"is_completed": False}

    async def complete_exercise(self, exercise_id, user_id):
        return None


@pytest.fixture
async def client(api_client_factory, monkeypatch):
    monkeypatch.setattr(
        training_api_module,
        "TrainingExerciseService",
        DummyTrainingExerciseSmokeService,
    )

    async def override_get_db():
        yield object()

    def override_get_current_user_id():
        return USER_ID

    async for async_client, _ in api_client_factory(
        training_api_module.router,
        dependency_overrides={
            get_db: override_get_db,
            get_current_user_id: override_get_current_user_id,
        },
    ):
        yield async_client


@pytest.mark.asyncio
async def test_training_exercise_list_smoke(client):
    response = await client.get("/training-exercises/")

    assert response.status_code == 200
    assert response.json()["exercises"][0]["id"] == str(EXERCISE_ID)


@pytest.mark.asyncio
async def test_training_exercise_detail_smoke(client):
    response = await client.get(f"/training-exercises/{EXERCISE_ID}")

    assert response.status_code == 200
    assert response.json()["title"] == "Detector"


@pytest.mark.asyncio
async def test_training_exercise_complete_smoke(client):
    response = await client.post(f"/training-exercises/{EXERCISE_ID}/complete")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
