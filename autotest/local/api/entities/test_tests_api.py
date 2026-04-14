import pytest

import src.api.tests as tests_api_module
from autotest4.factories.tests_entity import (
    ANSWER_ID,
    QUESTION_ID,
    RESULT_ID,
    SCALE_ID,
    SECOND_ANSWER_ID,
    SECOND_QUESTION_ID,
    SECOND_RESULT_ID,
    SECOND_TEST_ID,
    SECOND_USER_ID,
    TEST_ID,
    USER_ID,
    build_test_result_request,
    make_answer,
    make_border,
    make_question,
    make_scale,
    make_test,
    make_test_result_row,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.exceptions import (
    InvalidAnswersCountError,
    MyAppException,
    ObjectNotFoundException,
    ResultsScaleMismatchError,
    ScoreOutOfBoundsError,
)


class DummyTestApiService:
    auto_create_response = {"status": "OK"}
    all_tests_response = []
    test_by_id_response = None
    questions_response = []
    questions_with_answers_response = []
    answers_by_question_response = []
    details_response = None
    save_result_response = {"test_result_id": str(RESULT_ID), "result": []}
    result_by_user_and_test_response = []
    result_by_id_response = None
    passed_tests_response = []
    raise_on_auto_create = None
    raise_on_all_tests = None
    raise_on_test_by_id = None
    raise_on_questions = None
    raise_on_questions_with_answers = None
    raise_on_answers_by_question = None
    raise_on_details = None
    raise_on_save_result = None
    raise_on_result_by_user_and_test = None
    raise_on_result_by_id = None
    raise_on_passed_tests = None
    last_init_db = None
    last_test_by_id = None
    last_questions_test_id = None
    last_questions_with_answers_test_id = None
    last_answers_by_question_args = None
    last_details_test_id = None
    last_save_result_args = None
    last_result_by_user_and_test_args = None
    last_result_by_id = None
    last_passed_tests_user_id = None
    auto_create_called = False

    def __init__(self, db):
        self.db = db
        type(self).last_init_db = db

    @classmethod
    def reset(cls):
        cls.auto_create_response = {"status": "OK"}
        cls.all_tests_response = []
        cls.test_by_id_response = None
        cls.questions_response = []
        cls.questions_with_answers_response = []
        cls.answers_by_question_response = []
        cls.details_response = None
        cls.save_result_response = {"test_result_id": str(RESULT_ID), "result": []}
        cls.result_by_user_and_test_response = []
        cls.result_by_id_response = None
        cls.passed_tests_response = []
        cls.raise_on_auto_create = None
        cls.raise_on_all_tests = None
        cls.raise_on_test_by_id = None
        cls.raise_on_questions = None
        cls.raise_on_questions_with_answers = None
        cls.raise_on_answers_by_question = None
        cls.raise_on_details = None
        cls.raise_on_save_result = None
        cls.raise_on_result_by_user_and_test = None
        cls.raise_on_result_by_id = None
        cls.raise_on_passed_tests = None
        cls.last_init_db = None
        cls.last_test_by_id = None
        cls.last_questions_test_id = None
        cls.last_questions_with_answers_test_id = None
        cls.last_answers_by_question_args = None
        cls.last_details_test_id = None
        cls.last_save_result_args = None
        cls.last_result_by_user_and_test_args = None
        cls.last_result_by_id = None
        cls.last_passed_tests_user_id = None
        cls.auto_create_called = False

    async def auto_create(self):
        if type(self).raise_on_auto_create:
            raise type(self).raise_on_auto_create
        type(self).auto_create_called = True
        return type(self).auto_create_response

    async def all_tests(self):
        if type(self).raise_on_all_tests:
            raise type(self).raise_on_all_tests
        return type(self).all_tests_response

    async def test_by_id(self, test_id):
        if type(self).raise_on_test_by_id:
            raise type(self).raise_on_test_by_id
        type(self).last_test_by_id = test_id
        return type(self).test_by_id_response

    async def test_questions(self, test_id):
        if type(self).raise_on_questions:
            raise type(self).raise_on_questions
        type(self).last_questions_test_id = test_id
        return type(self).questions_response

    async def test_questions_with_answers(self, test_id):
        if type(self).raise_on_questions_with_answers:
            raise type(self).raise_on_questions_with_answers
        type(self).last_questions_with_answers_test_id = test_id
        return type(self).questions_with_answers_response

    async def answers_by_question_id(self, test_id, question_id):
        if type(self).raise_on_answers_by_question:
            raise type(self).raise_on_answers_by_question
        type(self).last_answers_by_question_args = (test_id, question_id)
        return type(self).answers_by_question_response

    async def details(self, test_id):
        if type(self).raise_on_details:
            raise type(self).raise_on_details
        type(self).last_details_test_id = test_id
        return type(self).details_response

    async def save_result(self, test_result_data, user_id):
        if type(self).raise_on_save_result:
            raise type(self).raise_on_save_result
        type(self).last_save_result_args = (test_result_data, user_id)
        return type(self).save_result_response

    async def get_test_result_by_user_and_test(self, test_id, user_id):
        if type(self).raise_on_result_by_user_and_test:
            raise type(self).raise_on_result_by_user_and_test
        type(self).last_result_by_user_and_test_args = (test_id, user_id)
        return type(self).result_by_user_and_test_response

    async def get_test_result_by_id(self, result_id):
        if type(self).raise_on_result_by_id:
            raise type(self).raise_on_result_by_id
        type(self).last_result_by_id = result_id
        return type(self).result_by_id_response

    async def get_passed_tests_by_user(self, user_id):
        if type(self).raise_on_passed_tests:
            raise type(self).raise_on_passed_tests
        type(self).last_passed_tests_user_id = user_id
        return type(self).passed_tests_response


@pytest.fixture
def tests_api_client_factory(api_client_factory, monkeypatch):
    DummyTestApiService.reset()
    monkeypatch.setattr(tests_api_module, "TestService", DummyTestApiService)

    def _factory(user_id=USER_ID):
        fake_db = object()

        async def override_get_db():
            yield fake_db

        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                tests_api_module.router,
                dependency_overrides={
                    get_db: override_get_db,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client, fake_db

        return _client()

    return _factory


@pytest.mark.asyncio
async def test_auto_create_returns_ok_and_calls_service(tests_api_client_factory):
    async for client, fake_db in tests_api_client_factory():
        response = await client.post("/tests/auto")

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    assert DummyTestApiService.auto_create_called is True
    assert DummyTestApiService.last_init_db is fake_db


@pytest.mark.asyncio
async def test_auto_create_returns_500_when_service_fails(tests_api_client_factory):
    DummyTestApiService.raise_on_auto_create = RuntimeError("auto failed")

    async for client, _ in tests_api_client_factory():
        response = await client.post("/tests/auto")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_all_tests_returns_service_payload(tests_api_client_factory):
    DummyTestApiService.all_tests_response = [
        {
            "id": str(TEST_ID),
            "title": "Burnout Test",
            "description": "Long description",
            "short_desc": "Short description",
            "link": "/images/test.png",
        }
    ]

    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(TEST_ID)
    assert sorted(response.json()[0].keys()) == ["description", "id", "link", "short_desc", "title"]


@pytest.mark.asyncio
async def test_all_tests_returns_empty_list_when_service_returns_empty(tests_api_client_factory):
    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_all_tests_returns_500_for_unexpected_service_error(tests_api_client_factory):
    DummyTestApiService.raise_on_all_tests = MyAppException()

    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_all_tests_returns_500_for_runtime_error(tests_api_client_factory):
    DummyTestApiService.raise_on_all_tests = RuntimeError("list failed")

    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_test_by_id_returns_detail_payload(tests_api_client_factory):
    DummyTestApiService.test_by_id_response = {
        "id": str(TEST_ID),
        "title": "Burnout Test",
        "description": "Long description",
        "short_desc": "Short description",
        "link": "/images/test.png",
        "scale": [],
    }

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(TEST_ID)
    assert DummyTestApiService.last_test_by_id == TEST_ID


@pytest.mark.asyncio
async def test_test_by_id_returns_404_when_service_reports_missing_object(tests_api_client_factory):
    DummyTestApiService.raise_on_test_by_id = ObjectNotFoundException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_test_by_id_returns_422_for_invalid_uuid(tests_api_client_factory):
    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests/not-a-uuid")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_test_by_id_returns_500_for_unexpected_service_error(tests_api_client_factory):
    DummyTestApiService.raise_on_test_by_id = MyAppException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_questions_returns_question_list(tests_api_client_factory):
    DummyTestApiService.questions_response = [
        {
            "id": str(QUESTION_ID),
            "text": "Question text",
            "opposite_text": "Opposite text",
            "number": 1,
            "test_id": str(TEST_ID),
            "answer_choice": [str(ANSWER_ID), str(SECOND_ANSWER_ID)],
        }
    ]

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/questions")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(QUESTION_ID)
    assert DummyTestApiService.last_questions_test_id == TEST_ID


@pytest.mark.asyncio
async def test_questions_returns_404_when_service_reports_missing_object(tests_api_client_factory):
    DummyTestApiService.raise_on_questions = ObjectNotFoundException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/questions")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_questions_returns_422_for_invalid_test_uuid(tests_api_client_factory):
    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests/not-a-uuid/questions")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_questions_returns_500_for_unexpected_service_error(tests_api_client_factory):
    DummyTestApiService.raise_on_questions = MyAppException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/questions")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_questions_with_answers_returns_payload(tests_api_client_factory):
    DummyTestApiService.questions_with_answers_response = [
        {
            "id": str(QUESTION_ID),
            "text": "Question text",
            "opposite_text": "Opposite text",
            "number": 1,
            "test_id": str(TEST_ID),
            "answer_choices": [
                {"id": str(ANSWER_ID), "text": "Never", "score": 0},
                {"id": str(SECOND_ANSWER_ID), "text": "Sometimes", "score": 1},
            ],
        }
    ]

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/questions/answers")

    assert response.status_code == 200
    assert len(response.json()[0]["answer_choices"]) == 2
    assert DummyTestApiService.last_questions_with_answers_test_id == TEST_ID


@pytest.mark.asyncio
async def test_questions_with_answers_returns_404_when_service_reports_missing_object(tests_api_client_factory):
    DummyTestApiService.raise_on_questions_with_answers = ObjectNotFoundException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/questions/answers")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_questions_with_answers_returns_422_for_invalid_test_uuid(tests_api_client_factory):
    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests/not-a-uuid/questions/answers")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_questions_with_answers_returns_500_for_unexpected_service_error(tests_api_client_factory):
    DummyTestApiService.raise_on_questions_with_answers = MyAppException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/questions/answers")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_answers_by_question_id_returns_answers(tests_api_client_factory):
    DummyTestApiService.answers_by_question_response = [
        [{"id": str(ANSWER_ID), "text": "Never", "score": 0}],
        [{"id": str(SECOND_ANSWER_ID), "text": "Sometimes", "score": 1}],
    ]

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/questions/{QUESTION_ID}/answers/")

    assert response.status_code == 200
    assert DummyTestApiService.last_answers_by_question_args == (TEST_ID, QUESTION_ID)


@pytest.mark.asyncio
async def test_answers_by_question_id_returns_404_when_service_reports_missing_object(tests_api_client_factory):
    DummyTestApiService.raise_on_answers_by_question = ObjectNotFoundException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/questions/{QUESTION_ID}/answers/")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_answers_by_question_id_returns_422_for_invalid_uuids(tests_api_client_factory):
    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests/not-a-uuid/questions/bad-uuid/answers/")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_answers_by_question_id_returns_500_for_unexpected_service_error(tests_api_client_factory):
    DummyTestApiService.raise_on_answers_by_question = MyAppException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/questions/{QUESTION_ID}/answers/")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_details_returns_nested_test_payload(tests_api_client_factory):
    DummyTestApiService.details_response = {
        "id": str(TEST_ID),
        "title": "Burnout Test",
        "description": "Long description",
        "short_desc": "Short description",
        "link": "/images/test.png",
        "scales": [
            {
                "id": str(SCALE_ID),
                "title": "Scale A",
                "min": 0,
                "max": 30,
                "borders": [
                    {
                        "id": "1b3f7146-3c7f-4aaa-a4b5-8f0baf268701",
                        "left_border": 0,
                        "right_border": 10,
                        "color": "#00AA00",
                        "title": "Norm",
                        "user_recommendation": "Take care",
                    }
                ],
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

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/details")

    assert response.status_code == 200
    assert response.json()["scales"][0]["id"] == str(SCALE_ID)
    assert DummyTestApiService.last_details_test_id == TEST_ID


@pytest.mark.asyncio
async def test_details_returns_404_when_service_reports_missing_object(tests_api_client_factory):
    DummyTestApiService.raise_on_details = ObjectNotFoundException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/details")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_details_returns_422_for_invalid_test_uuid(tests_api_client_factory):
    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests/not-a-uuid/details")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_details_returns_500_for_unexpected_service_error(tests_api_client_factory):
    DummyTestApiService.raise_on_details = MyAppException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/details")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_save_result_returns_saved_payload(tests_api_client_factory):
    DummyTestApiService.save_result_response = {
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

    async for client, _ in tests_api_client_factory():
        response = await client.post("/tests/result", json=build_test_result_request())

    assert response.status_code == 200
    assert response.json()["test_result_id"] == str(RESULT_ID)
    assert DummyTestApiService.last_save_result_args[1] == USER_ID
    assert DummyTestApiService.last_save_result_args[0].test_id == TEST_ID


@pytest.mark.asyncio
async def test_save_result_returns_404_when_service_reports_missing_object(tests_api_client_factory):
    DummyTestApiService.raise_on_save_result = ObjectNotFoundException()

    async for client, _ in tests_api_client_factory():
        response = await client.post("/tests/result", json=build_test_result_request())

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_save_result_returns_400_when_answers_count_is_invalid(tests_api_client_factory):
    DummyTestApiService.raise_on_save_result = InvalidAnswersCountError()

    async for client, _ in tests_api_client_factory():
        response = await client.post("/tests/result", json=build_test_result_request())

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_save_result_returns_500_when_scale_count_mismatch_occurs(tests_api_client_factory):
    DummyTestApiService.raise_on_save_result = ResultsScaleMismatchError()

    async for client, _ in tests_api_client_factory():
        response = await client.post("/tests/result", json=build_test_result_request())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_save_result_returns_400_when_score_is_out_of_bounds(tests_api_client_factory):
    DummyTestApiService.raise_on_save_result = ScoreOutOfBoundsError()

    async for client, _ in tests_api_client_factory():
        response = await client.post("/tests/result", json=build_test_result_request())

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_save_result_returns_500_for_domain_error_wrapped_as_my_app_exception(tests_api_client_factory):
    DummyTestApiService.raise_on_save_result = MyAppException()

    async for client, _ in tests_api_client_factory():
        response = await client.post("/tests/result", json=build_test_result_request())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_save_result_returns_422_for_invalid_request_payload(tests_api_client_factory):
    async for client, _ in tests_api_client_factory():
        response = await client.post("/tests/result", json={"test_id": "bad", "date": "bad", "results": "bad"})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_save_result_returns_422_when_required_field_missing(tests_api_client_factory):
    payload = build_test_result_request()
    payload.pop("results")

    async for client, _ in tests_api_client_factory():
        response = await client.post("/tests/result", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_save_result_returns_422_for_empty_body(tests_api_client_factory):
    async for client, _ in tests_api_client_factory():
        response = await client.post("/tests/result", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_result_by_user_and_test_uses_current_user_when_query_user_missing(tests_api_client_factory):
    DummyTestApiService.result_by_user_and_test_response = [
        {
            "test_id": str(TEST_ID),
            "test_result_id": str(RESULT_ID),
            "datetime": "2026-04-15T10:00:00",
            "scale_results": [],
        }
    ]

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/results/")

    assert response.status_code == 200
    assert DummyTestApiService.last_result_by_user_and_test_args == (TEST_ID, USER_ID)


@pytest.mark.asyncio
async def test_result_by_user_and_test_accepts_explicit_user_id(tests_api_client_factory):
    DummyTestApiService.result_by_user_and_test_response = []

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/results/?user_id={SECOND_USER_ID}")

    assert response.status_code == 200
    assert DummyTestApiService.last_result_by_user_and_test_args == (TEST_ID, SECOND_USER_ID)


@pytest.mark.asyncio
async def test_result_by_user_and_test_returns_404_when_service_reports_missing_object(tests_api_client_factory):
    DummyTestApiService.raise_on_result_by_user_and_test = ObjectNotFoundException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/results/")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_result_by_user_and_test_returns_422_for_invalid_uuid_inputs(tests_api_client_factory):
    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests/not-a-uuid/results/?user_id=bad-uuid")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_result_by_user_and_test_returns_500_for_unexpected_service_error(tests_api_client_factory):
    DummyTestApiService.raise_on_result_by_user_and_test = MyAppException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/{TEST_ID}/results/")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_test_result_by_id_returns_payload(tests_api_client_factory):
    DummyTestApiService.result_by_id_response = {
        "test_id": str(TEST_ID),
        "test_result_id": str(RESULT_ID),
        "datetime": "2026-04-15T10:00:00",
        "scale_results": [],
    }

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/test_result/{RESULT_ID}")

    assert response.status_code == 200
    assert DummyTestApiService.last_result_by_id == RESULT_ID


@pytest.mark.asyncio
async def test_get_test_result_by_id_returns_404_when_service_reports_missing_object(tests_api_client_factory):
    DummyTestApiService.raise_on_result_by_id = ObjectNotFoundException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/test_result/{RESULT_ID}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_test_result_by_id_returns_422_for_invalid_result_uuid(tests_api_client_factory):
    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests/test_result/not-a-uuid")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_test_result_by_id_returns_500_for_unexpected_service_error(tests_api_client_factory):
    DummyTestApiService.raise_on_result_by_id = MyAppException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/test_result/{RESULT_ID}")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_passed_tests_by_user_returns_payload(tests_api_client_factory):
    DummyTestApiService.passed_tests_response = [
        {
            "title": "Burnout Test",
            "description": "Long description",
            "test_id": str(TEST_ID),
            "link": "/images/test.png",
        }
    ]

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/passed/user/{SECOND_USER_ID}")

    assert response.status_code == 200
    assert sorted(response.json()[0].keys()) == ["description", "link", "test_id", "title"]
    assert DummyTestApiService.last_passed_tests_user_id == SECOND_USER_ID


@pytest.mark.asyncio
async def test_get_passed_tests_by_user_returns_404_when_service_reports_missing_object(tests_api_client_factory):
    DummyTestApiService.raise_on_passed_tests = ObjectNotFoundException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/passed/user/{SECOND_USER_ID}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_passed_tests_by_user_returns_422_for_invalid_user_uuid(tests_api_client_factory):
    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests/passed/user/not-a-uuid")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_passed_tests_by_user_returns_500_for_unexpected_service_error(tests_api_client_factory):
    DummyTestApiService.raise_on_passed_tests = MyAppException()

    async for client, _ in tests_api_client_factory():
        response = await client.get(f"/tests/passed/user/{SECOND_USER_ID}")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_passed_tests_for_current_user_uses_current_user_id(tests_api_client_factory):
    DummyTestApiService.passed_tests_response = [
        {
            "title": "Burnout Test",
            "description": "Long description",
            "test_id": str(TEST_ID),
            "link": "/images/test.png",
        }
    ]

    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests/passed/user")

    assert response.status_code == 200
    assert sorted(response.json()[0].keys()) == ["description", "link", "test_id", "title"]
    assert DummyTestApiService.last_passed_tests_user_id == USER_ID


@pytest.mark.asyncio
async def test_get_passed_tests_for_current_user_returns_empty_list_when_service_returns_empty(
    tests_api_client_factory,
):
    DummyTestApiService.passed_tests_response = []

    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests/passed/user")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_passed_tests_for_current_user_should_return_404_when_service_reports_missing_object(
    tests_api_client_factory,
):
    DummyTestApiService.raise_on_passed_tests = ObjectNotFoundException()

    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests/passed/user")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_passed_tests_for_current_user_returns_500_for_unexpected_service_error(
    tests_api_client_factory,
):
    DummyTestApiService.raise_on_passed_tests = MyAppException()

    async for client, _ in tests_api_client_factory():
        response = await client.get("/tests/passed/user")

    assert response.status_code == 500
