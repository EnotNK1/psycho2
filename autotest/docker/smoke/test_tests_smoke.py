import pytest

import src.api.tests as tests_api_module
from autotest.factories.tests_entity import (
    ANSWER_ID,
    QUESTION_ID,
    RESULT_ID,
    SCALE_ID,
    SECOND_ANSWER_ID,
    TEST_ID,
    USER_ID,
    build_test_result_request,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id


class DummyTestsSmokeService:
    def __init__(self, db):
        self.db = db

    async def auto_create(self):
        return {"status": "OK"}

    async def all_tests(self):
        return [
            {
                "id": str(TEST_ID),
                "title": "Burnout Test",
                "description": "Long description",
                "short_desc": "Short description",
                "link": "/images/test.png",
            }
        ]

    async def test_by_id(self, test_id):
        return {
            "id": str(test_id),
            "title": "Burnout Test",
            "description": "Long description",
            "short_desc": "Short description",
            "link": "/images/test.png",
            "scale": [],
        }

    async def test_questions(self, test_id):
        return [
            {
                "id": str(QUESTION_ID),
                "text": "Question text",
                "opposite_text": "Opposite text",
                "number": 1,
                "test_id": str(test_id),
                "answer_choice": [str(ANSWER_ID), str(SECOND_ANSWER_ID)],
            }
        ]

    async def test_questions_with_answers(self, test_id):
        return [
            {
                "id": str(QUESTION_ID),
                "text": "Question text",
                "opposite_text": "Opposite text",
                "number": 1,
                "test_id": str(test_id),
                "answer_choices": [
                    {"id": str(ANSWER_ID), "text": "Never", "score": 0},
                    {"id": str(SECOND_ANSWER_ID), "text": "Sometimes", "score": 1},
                ],
            }
        ]

    async def answers_by_question_id(self, test_id, question_id):
        return [[{"id": str(ANSWER_ID), "text": "Never", "score": 0}]]

    async def details(self, test_id):
        return {
            "id": str(test_id),
            "title": "Burnout Test",
            "description": "Long description",
            "short_desc": "Short description",
            "link": "/images/test.png",
            "scales": [
                {
                    "id": str(SCALE_ID),
                    "title": "Scale A",
                    "min": 0,
                    "max": 10,
                    "borders": [],
                }
            ],
            "questions": [
                {
                    "id": str(QUESTION_ID),
                    "text": "Question text",
                    "opposite_text": "Opposite text",
                    "number": 1,
                    "answers": [{"id": str(ANSWER_ID), "text": "Never", "score": 0}],
                }
            ],
        }

    async def save_result(self, test_result_data, user_id):
        return {
            "test_result_id": str(RESULT_ID),
            "result": [
                {
                    "scale_id": str(SCALE_ID),
                    "scale_title": "Scale A",
                    "score": 7,
                    "conclusion": "Norm",
                    "color": "#00AA00",
                    "user_recommendation": "Take care",
                }
            ],
        }

    async def get_test_result_by_user_and_test(self, test_id, user_id):
        return [
            {
                "test_id": str(test_id),
                "test_result_id": str(RESULT_ID),
                "datetime": "2026-04-15T10:00:00",
                "scale_results": [],
            }
        ]

    async def get_test_result_by_id(self, result_id):
        return {
            "test_id": str(TEST_ID),
            "test_result_id": str(result_id),
            "datetime": "2026-04-15T10:00:00",
            "scale_results": [],
        }

    async def get_passed_tests_by_user(self, user_id):
        return [
            {
                "title": "Burnout Test",
                "description": "Long description",
                "test_id": str(TEST_ID),
                "link": "/images/test.png",
            }
        ]


@pytest.fixture
async def client(api_client_factory, monkeypatch):
    monkeypatch.setattr(tests_api_module, "TestService", DummyTestsSmokeService)

    async def override_get_db():
        yield object()

    def override_get_current_user_id():
        return USER_ID

    async for async_client, _ in api_client_factory(
        tests_api_module.router,
        dependency_overrides={
            get_db: override_get_db,
            get_current_user_id: override_get_current_user_id,
        },
    ):
        yield async_client


@pytest.mark.asyncio
async def test_tests_list_smoke(client):
    response = await client.get("/tests")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(TEST_ID)


@pytest.mark.asyncio
async def test_tests_detail_smoke(client):
    response = await client.get(f"/tests/{TEST_ID}")

    assert response.status_code == 200
    assert response.json()["title"] == "Burnout Test"


@pytest.mark.asyncio
async def test_tests_save_result_smoke(client):
    response = await client.post("/tests/result", json=build_test_result_request())

    assert response.status_code == 200
    assert response.json()["test_result_id"] == str(RESULT_ID)


@pytest.mark.asyncio
async def test_tests_result_by_id_smoke(client):
    response = await client.get(f"/tests/test_result/{RESULT_ID}")

    assert response.status_code == 200
    assert response.json()["test_result_id"] == str(RESULT_ID)


@pytest.mark.asyncio
async def test_tests_passed_current_user_smoke(client):
    response = await client.get("/tests/passed/user")

    assert response.status_code == 200
    assert response.json()[0]["test_id"] == str(TEST_ID)
