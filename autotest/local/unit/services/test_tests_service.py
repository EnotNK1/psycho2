import datetime
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import src.services.tests as tests_service_module
from autotest4.factories.tests_entity import (
    ANSWER_ID,
    BORDER_ID,
    QUESTION_ID,
    RESULT_ID,
    SCALE_ID,
    SECOND_ANSWER_ID,
    SECOND_BORDER_ID,
    SECOND_QUESTION_ID,
    SECOND_RESULT_ID,
    SECOND_SCALE_ID,
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
    make_scale_result_row,
)
from src.exceptions import (
    InvalidAnswersCountError,
    MyAppException,
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    ResultsScaleMismatchError,
    ScoreOutOfBoundsError,
)
from src.services.tests import TestService


class FakeRepository:
    def __init__(self):
        self.one_result = None
        self.one_or_none_result = None
        self.filtered_result = []
        self.all_result = []
        self.by_ids_result = []
        self.add_calls = []
        self.delete_calls = []
        self.get_one_calls = []
        self.get_one_or_none_calls = []
        self.get_filtered_calls = []
        self.get_all_calls = 0
        self.get_by_ids_calls = []
        self.raise_on_add = None
        self.raise_on_get_one = None
        self.raise_on_get_one_or_none = None
        self.raise_on_get_filtered = None
        self.raise_on_get_all = None
        self.raise_on_get_by_ids = None
        self.raise_on_delete = None

    async def add(self, data):
        if self.raise_on_add:
            raise self.raise_on_add
        self.add_calls.append(data)

    async def delete(self, **filter_by):
        if self.raise_on_delete:
            raise self.raise_on_delete
        self.delete_calls.append(filter_by)

    async def get_one(self, *args, **filter_by):
        if self.raise_on_get_one:
            raise self.raise_on_get_one
        self.get_one_calls.append((args, filter_by))
        return self.one_result

    async def get_one_or_none(self, **filter_by):
        if self.raise_on_get_one_or_none:
            raise self.raise_on_get_one_or_none
        self.get_one_or_none_calls.append(filter_by)
        return self.one_or_none_result

    async def get_filtered(self, **filter_by):
        if self.raise_on_get_filtered:
            raise self.raise_on_get_filtered
        self.get_filtered_calls.append(filter_by)
        return self.filtered_result

    async def get_all(self):
        if self.raise_on_get_all:
            raise self.raise_on_get_all
        self.get_all_calls += 1
        return self.all_result

    async def get_by_ids(self, ids):
        if self.raise_on_get_by_ids:
            raise self.raise_on_get_by_ids
        self.get_by_ids_calls.append(ids)
        return self.by_ids_result


class FakeSession:
    def __init__(self):
        self.flush_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.flush_should_raise = None
        self.commit_should_raise = None

    async def flush(self):
        if self.flush_should_raise:
            raise self.flush_should_raise
        self.flush_count += 1

    async def commit(self):
        if self.commit_should_raise:
            raise self.commit_should_raise
        self.commit_count += 1

    async def rollback(self):
        self.rollback_count += 1


class FakeTestsDb:
    def __init__(self):
        self.tests = FakeRepository()
        self.question = FakeRepository()
        self.answer_choice = FakeRepository()
        self.scales = FakeRepository()
        self.borders = FakeRepository()
        self.test_result = FakeRepository()
        self.scale_result = FakeRepository()
        self.ontology_entry = FakeRepository()
        self.session = FakeSession()
        self.commit_count = 0
        self.rollback_count = 0

    async def commit(self):
        self.commit_count += 1

    async def rollback(self):
        self.rollback_count += 1


class DummyInquiryService:
    calls = []

    def __init__(self, db):
        self.db = db

    async def check_and_create_inquiries(self, data):
        type(self).calls.append(data)


class DummyEmojiService:
    calls = []

    def __init__(self, db):
        self.db = db

    async def check_and_create_emojis(self, data):
        type(self).calls.append(data)


class DummyGamificationService:
    calls = []

    def __init__(self, db):
        self.db = db

    async def add_points_for_activity(self, user_id, activity):
        type(self).calls.append((user_id, activity))
        return 15


@pytest.fixture
def fake_tests_db():
    return FakeTestsDb()


@pytest.fixture(autouse=True)
def reset_dummy_side_effects():
    DummyInquiryService.calls = []
    DummyEmojiService.calls = []
    DummyGamificationService.calls = []


def build_test_add_payload(test_id=TEST_ID, title="Burnout Test"):
    return {
        "id": str(test_id),
        "title": title,
        "description": "Long description",
        "short_desc": "Short",
        "link": "/images/test.png",
    }


def build_scale_add_payload(scale_id=SCALE_ID, test_id=TEST_ID, title="Scale A"):
    return {
        "id": str(scale_id),
        "title": title,
        "min": 0,
        "max": 10,
        "test_id": str(test_id),
    }


def build_answer_payload(answer_id=ANSWER_ID, text="Never", score=0):
    return {"id": str(answer_id), "text": text, "score": score}


def build_question_payload(question_id=QUESTION_ID, test_id=TEST_ID, answer_choice=None):
    return {
        "id": str(question_id),
        "text": "Question text",
        "opposite_text": "Opposite text",
        "number": 1,
        "test_id": str(test_id),
        "answer_choice": answer_choice or [str(ANSWER_ID), str(SECOND_ANSWER_ID)],
    }


@pytest.mark.asyncio
async def test_service_auto_create_reads_sources_and_commits(fake_tests_db, monkeypatch):
    calls = []

    async def fake_add_tests(self, data):
        calls.append(("tests", data))

    async def fake_add_scales(self, data):
        calls.append(("scales", data))

    async def fake_add_answers(self, data):
        calls.append(("answers", data))

    async def fake_add_questions(self, data):
        calls.append(("questions", data))

    monkeypatch.setattr(TestService, "add_tests", fake_add_tests)
    monkeypatch.setattr(TestService, "add_scales_and_borders", fake_add_scales)
    monkeypatch.setattr(TestService, "add_answer_choices", fake_add_answers)
    monkeypatch.setattr(TestService, "add_questions", fake_add_questions)
    monkeypatch.setattr(tests_service_module, "InquiryService", DummyInquiryService)
    monkeypatch.setattr(tests_service_module, "EmojiService", DummyEmojiService)
    payload_map = {
        "src/services/info/test_info.json": [{"id": "test"}],
        "src/services/info/scale_info.json": [{"id": "scale"}],
        "src/services/info/answer_choices_info.json": [{"id": "answer"}],
        "src/services/info/questions_info.json": [{"id": "question"}],
        "src/services/info/inquiry.json": [{"id": "inquiry"}],
        "src/services/info/emoji.json": [{"id": "emoji"}],
    }

    class DummyFile:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            import json

            return json.dumps(payload_map[self.path])

    monkeypatch.setattr("builtins.open", lambda path, encoding=None: DummyFile(path))

    result = await TestService(fake_tests_db).auto_create()

    assert result["status"] == "OK"
    assert fake_tests_db.commit_count == 1
    assert [name for name, _ in calls] == ["tests", "scales", "answers", "questions"]
    assert DummyInquiryService.calls == [[{"id": "inquiry"}]]
    assert DummyEmojiService.calls == [[{"id": "emoji"}]]


def test_service_load_borders_for_scale_filters_json_by_scale_id(tmp_path, monkeypatch):
    payload = [
        {"id": str(BORDER_ID), "scale_id": str(SCALE_ID)},
        {"id": str(SECOND_BORDER_ID), "scale_id": str(SECOND_SCALE_ID)},
    ]

    class DummyFile:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(payload)

    monkeypatch.setattr("builtins.open", lambda path, encoding=None: DummyFile())

    result = TestService().load_borders_for_scale(SCALE_ID)

    assert result == [{"id": str(BORDER_ID), "scale_id": str(SCALE_ID)}]


@pytest.mark.asyncio
async def test_service_add_tests_adds_only_missing_records(fake_tests_db):
    responses = [None, make_test(test_id=SECOND_TEST_ID)]

    async def get_one_or_none(**filter_by):
        return responses.pop(0)

    fake_tests_db.tests.get_one_or_none = get_one_or_none

    await TestService(fake_tests_db).add_tests(
        [build_test_add_payload(TEST_ID), build_test_add_payload(SECOND_TEST_ID, title="Stress Test")]
    )

    assert len(fake_tests_db.tests.add_calls) == 1
    assert fake_tests_db.tests.add_calls[0].id == TEST_ID


@pytest.mark.asyncio
async def test_service_add_tests_skips_existing_object_already_exists_error(fake_tests_db):
    fake_tests_db.tests.raise_on_add = ObjectAlreadyExistsException()

    await TestService(fake_tests_db).add_tests([build_test_add_payload(TEST_ID)])

    assert fake_tests_db.rollback_count == 0


@pytest.mark.asyncio
async def test_service_add_tests_rolls_back_and_raises_my_app_for_unexpected_error(fake_tests_db):
    fake_tests_db.tests.raise_on_add = RuntimeError("db failed")

    with pytest.raises(MyAppException):
        await TestService(fake_tests_db).add_tests([build_test_add_payload(TEST_ID)])

    assert fake_tests_db.rollback_count == 1


@pytest.mark.asyncio
async def test_service_add_scales_and_borders_creates_scale_and_recreates_borders(fake_tests_db, monkeypatch):
    monkeypatch.setattr(
        TestService,
        "load_borders_for_scale",
        lambda self, scale_id: [
            {
                "id": str(BORDER_ID),
                "left_border": 0,
                "right_border": 10,
                "color": "#00AA00",
                "title": "Norm",
                "user_recommendation": "Take care",
                "scale_id": str(scale_id),
            }
        ],
    )
    fake_tests_db.tests.one_or_none_result = make_test()
    fake_tests_db.scales.one_or_none_result = None
    fake_tests_db.borders.raise_on_delete = ObjectNotFoundException()

    await TestService(fake_tests_db).add_scales_and_borders([build_scale_add_payload()])

    assert len(fake_tests_db.scales.add_calls) == 1
    assert len(fake_tests_db.borders.add_calls) == 1


@pytest.mark.asyncio
async def test_service_add_scales_and_borders_skips_scale_without_test_id(fake_tests_db):
    await TestService(fake_tests_db).add_scales_and_borders(
        [{"id": str(SCALE_ID), "title": "Scale A", "min": 0, "max": 10, "test_id": None}]
    )

    assert fake_tests_db.scales.add_calls == []


@pytest.mark.asyncio
async def test_service_add_scales_and_borders_skips_when_parent_test_missing(fake_tests_db):
    fake_tests_db.tests.one_or_none_result = None

    await TestService(fake_tests_db).add_scales_and_borders([build_scale_add_payload()])

    assert fake_tests_db.scales.add_calls == []


@pytest.mark.asyncio
async def test_service_add_scales_and_borders_rolls_back_and_raises_my_app(fake_tests_db, monkeypatch):
    monkeypatch.setattr(TestService, "load_borders_for_scale", lambda self, scale_id: [])
    fake_tests_db.tests.one_or_none_result = make_test()
    fake_tests_db.scales.raise_on_add = RuntimeError("scale add failed")

    with pytest.raises(MyAppException):
        await TestService(fake_tests_db).add_scales_and_borders([build_scale_add_payload()])

    assert fake_tests_db.rollback_count == 1


@pytest.mark.asyncio
async def test_service_add_answer_choices_adds_only_missing(fake_tests_db):
    responses = [None, make_answer(answer_id=SECOND_ANSWER_ID)]

    async def get_one_or_none(**filter_by):
        return responses.pop(0)

    fake_tests_db.answer_choice.get_one_or_none = get_one_or_none

    await TestService(fake_tests_db).add_answer_choices(
        [build_answer_payload(ANSWER_ID), build_answer_payload(SECOND_ANSWER_ID, text="Sometimes", score=1)]
    )

    assert len(fake_tests_db.answer_choice.add_calls) == 1
    assert fake_tests_db.answer_choice.add_calls[0].id == ANSWER_ID


@pytest.mark.asyncio
async def test_service_add_answer_choices_rolls_back_and_raises_my_app(fake_tests_db):
    fake_tests_db.answer_choice.raise_on_add = RuntimeError("answer add failed")

    with pytest.raises(MyAppException):
        await TestService(fake_tests_db).add_answer_choices([build_answer_payload()])

    assert fake_tests_db.rollback_count == 1


@pytest.mark.asyncio
async def test_service_add_questions_adds_only_missing(fake_tests_db):
    responses = [None, make_question(question_id=SECOND_QUESTION_ID)]

    async def get_one_or_none(**filter_by):
        return responses.pop(0)

    fake_tests_db.question.get_one_or_none = get_one_or_none

    await TestService(fake_tests_db).add_questions(
        [
            build_question_payload(QUESTION_ID),
            build_question_payload(SECOND_QUESTION_ID),
        ]
    )

    assert len(fake_tests_db.question.add_calls) == 1
    assert fake_tests_db.question.add_calls[0].id == QUESTION_ID


@pytest.mark.asyncio
async def test_service_add_questions_rolls_back_and_raises_my_app(fake_tests_db):
    fake_tests_db.question.raise_on_add = RuntimeError("question add failed")

    with pytest.raises(MyAppException):
        await TestService(fake_tests_db).add_questions([build_question_payload()])

    assert fake_tests_db.rollback_count == 1


@pytest.mark.asyncio
async def test_service_all_tests_returns_serialized_list(fake_tests_db):
    fake_tests_db.tests.all_result = [make_test(), make_test(test_id=SECOND_TEST_ID, title="Stress Test")]

    result = await TestService(fake_tests_db).all_tests()

    assert [item["title"] for item in result] == ["Burnout Test", "Stress Test"]


@pytest.mark.asyncio
async def test_service_all_tests_wraps_unexpected_error(fake_tests_db):
    fake_tests_db.tests.raise_on_get_all = RuntimeError("db failed")

    with pytest.raises(MyAppException):
        await TestService(fake_tests_db).all_tests()

    assert fake_tests_db.rollback_count == 1


@pytest.mark.asyncio
async def test_service_test_by_id_returns_test(fake_tests_db):
    fake_tests_db.tests.one_result = make_test()

    result = await TestService(fake_tests_db).test_by_id(TEST_ID)

    assert result.id == TEST_ID


@pytest.mark.asyncio
async def test_service_test_by_id_raises_not_found_for_missing_test(fake_tests_db):
    with pytest.raises(ObjectNotFoundException):
        await TestService(fake_tests_db).test_by_id(TEST_ID)


@pytest.mark.asyncio
async def test_service_test_questions_returns_question_payload(fake_tests_db):
    fake_tests_db.question.filtered_result = [make_question()]

    result = await TestService(fake_tests_db).test_questions(TEST_ID)

    assert result[0]["id"] == QUESTION_ID
    assert result[0]["answer_choice"] == [ANSWER_ID, SECOND_ANSWER_ID]


@pytest.mark.asyncio
async def test_service_test_questions_raises_not_found_when_empty(fake_tests_db):
    with pytest.raises(ObjectNotFoundException):
        await TestService(fake_tests_db).test_questions(TEST_ID)


@pytest.mark.asyncio
async def test_service_test_questions_with_answers_returns_answers(fake_tests_db):
    fake_tests_db.question.filtered_result = [make_question(answer_choice=[ANSWER_ID, SECOND_ANSWER_ID])]
    fake_tests_db.answer_choice.by_ids_result = [
        make_answer(answer_id=ANSWER_ID, text="Never", score=0),
        make_answer(answer_id=SECOND_ANSWER_ID, text="Sometimes", score=1),
    ]

    result = await TestService(fake_tests_db).test_questions_with_answers(TEST_ID)

    assert len(result[0]["answer_choices"]) == 2
    assert fake_tests_db.answer_choice.get_by_ids_calls == [[ANSWER_ID, SECOND_ANSWER_ID]]


@pytest.mark.asyncio
async def test_service_test_questions_with_answers_omits_missing_answer_ids(fake_tests_db):
    fake_tests_db.question.filtered_result = [make_question(answer_choice=[ANSWER_ID, SECOND_ANSWER_ID])]
    fake_tests_db.answer_choice.by_ids_result = [make_answer(answer_id=ANSWER_ID, text="Never", score=0)]

    result = await TestService(fake_tests_db).test_questions_with_answers(TEST_ID)

    assert len(result[0]["answer_choices"]) == 1
    assert result[0]["answer_choices"][0]["id"] == ANSWER_ID


@pytest.mark.asyncio
async def test_service_test_questions_with_answers_raises_not_found_when_questions_missing(fake_tests_db):
    with pytest.raises(ObjectNotFoundException):
        await TestService(fake_tests_db).test_questions_with_answers(TEST_ID)


@pytest.mark.asyncio
async def test_service_answers_by_question_id_returns_answers(fake_tests_db):
    fake_tests_db.tests.one_or_none_result = make_test()
    fake_tests_db.question.one_or_none_result = make_question(answer_choice=[ANSWER_ID, SECOND_ANSWER_ID])

    async def get_filtered(**filter_by):
        if filter_by["id"] == ANSWER_ID:
            return [make_answer(answer_id=ANSWER_ID, text="Never", score=0)]
        return [make_answer(answer_id=SECOND_ANSWER_ID, text="Sometimes", score=1)]

    fake_tests_db.answer_choice.get_filtered = get_filtered

    result = await TestService(fake_tests_db).answers_by_question_id(TEST_ID, QUESTION_ID)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_service_answers_by_question_id_raises_not_found_when_test_missing(fake_tests_db):
    with pytest.raises(ObjectNotFoundException):
        await TestService(fake_tests_db).answers_by_question_id(TEST_ID, QUESTION_ID)


@pytest.mark.asyncio
async def test_service_answers_by_question_id_should_raise_not_found_when_answers_missing(fake_tests_db):
    fake_tests_db.tests.one_or_none_result = make_test()
    fake_tests_db.question.one_or_none_result = make_question(answer_choice=[])

    with pytest.raises(ObjectNotFoundException):
        await TestService(fake_tests_db).answers_by_question_id(TEST_ID, QUESTION_ID)


@pytest.mark.asyncio
async def test_service_details_returns_nested_structure(fake_tests_db):
    fake_tests_db.tests.one_result = make_test()
    fake_tests_db.scales.filtered_result = [make_scale()]
    fake_tests_db.borders.filtered_result = [make_border()]
    fake_tests_db.question.filtered_result = [make_question(answer_choice=[ANSWER_ID])]
    fake_tests_db.answer_choice.filtered_result = [make_answer()]

    result = await TestService(fake_tests_db).details(TEST_ID)

    assert result.id == TEST_ID
    assert result.scales[0].borders[0].id == BORDER_ID
    assert result.questions[0].answers[0].id == ANSWER_ID


@pytest.mark.asyncio
async def test_service_details_should_include_all_answers_for_question(fake_tests_db):
    fake_tests_db.tests.one_result = make_test()
    fake_tests_db.scales.filtered_result = [make_scale()]
    fake_tests_db.borders.filtered_result = [make_border()]
    fake_tests_db.question.filtered_result = [make_question(answer_choice=[ANSWER_ID, SECOND_ANSWER_ID])]

    async def get_filtered(**filter_by):
        if "scale_id" in filter_by:
            return [make_border()]
        if filter_by["id"] == ANSWER_ID:
            return [make_answer(answer_id=ANSWER_ID, text="Never", score=0)]
        return [make_answer(answer_id=SECOND_ANSWER_ID, text="Sometimes", score=1)]

    fake_tests_db.borders.get_filtered = get_filtered
    fake_tests_db.answer_choice.get_filtered = get_filtered

    result = await TestService(fake_tests_db).details(TEST_ID)

    assert len(result.questions[0].answers) == 2


@pytest.mark.asyncio
async def test_service_details_raises_not_found_when_test_missing(fake_tests_db):
    with pytest.raises(ObjectNotFoundException):
        await TestService(fake_tests_db).details(TEST_ID)


@pytest.mark.asyncio
async def test_service_save_result_returns_calculated_payload(fake_tests_db, monkeypatch):
    fake_tests_db.tests.one_result = make_test(title="Определяем выгорание на работе")
    fake_tests_db.question.filtered_result = [make_question(question_id=QUESTION_ID), make_question(question_id=SECOND_QUESTION_ID, number=2)]
    fake_tests_db.scales.filtered_result = [make_scale()]

    async def borders_get_filtered(**filter_by):
        return [make_border(scale_id=SCALE_ID, left_border=0, right_border=10, title="Norm")]

    fake_tests_db.borders.get_filtered = borders_get_filtered
    async def ontology_get_filtered(**filter_by):
        return []

    fake_tests_db.ontology_entry.get_filtered = ontology_get_filtered
    monkeypatch.setattr(tests_service_module.calculator_service, "test_maslach_calculate_results", lambda results: [7])
    monkeypatch.setattr(tests_service_module, "GamificationService", DummyGamificationService)
    monkeypatch.setattr(tests_service_module, "recommendations", lambda payload: [])
    monkeypatch.setattr(
        tests_service_module,
        "load_data",
        lambda path: [],
    )

    result = await TestService(fake_tests_db).save_result(
        tests_service_module.TestResultRequest.model_validate(build_test_result_request(results=[0, 1])),
        USER_ID,
    )

    assert result["test_result_id"]
    assert result["result"][0]["score"] == 7
    assert fake_tests_db.session.flush_count == 1
    assert fake_tests_db.session.commit_count == 1
    assert DummyGamificationService.calls == [(USER_ID, "test_completed")]


@pytest.mark.asyncio
async def test_service_save_result_raises_for_invalid_answers_count(fake_tests_db):
    fake_tests_db.tests.one_result = make_test(title="Burnout Test")
    fake_tests_db.question.filtered_result = [make_question()]

    with pytest.raises(InvalidAnswersCountError):
        await TestService(fake_tests_db).save_result(
            tests_service_module.TestResultRequest.model_validate(build_test_result_request(results=[0, 1])),
            USER_ID,
        )


@pytest.mark.asyncio
async def test_service_save_result_raises_for_scale_mismatch(fake_tests_db, monkeypatch):
    fake_tests_db.tests.one_result = make_test(title="Определяем выгорание на работе")
    fake_tests_db.question.filtered_result = [make_question(), make_question(question_id=SECOND_QUESTION_ID, number=2)]
    fake_tests_db.scales.filtered_result = [make_scale(), make_scale(scale_id=SECOND_SCALE_ID, title="Scale B")]
    monkeypatch.setattr(tests_service_module.calculator_service, "test_maslach_calculate_results", lambda results: [7])

    with pytest.raises(ResultsScaleMismatchError):
        await TestService(fake_tests_db).save_result(
            tests_service_module.TestResultRequest.model_validate(build_test_result_request(results=[0, 1])),
            USER_ID,
        )


@pytest.mark.asyncio
async def test_service_save_result_raises_for_score_out_of_bounds(fake_tests_db, monkeypatch):
    fake_tests_db.tests.one_result = make_test(title="Определяем выгорание на работе")
    fake_tests_db.question.filtered_result = [make_question(), make_question(question_id=SECOND_QUESTION_ID, number=2)]
    fake_tests_db.scales.filtered_result = [make_scale(min_score=0, max_score=5)]
    async def borders_get_filtered(**filter_by):
        return [make_border(scale_id=SCALE_ID, left_border=0, right_border=5)]

    async def ontology_get_filtered(**filter_by):
        return []

    fake_tests_db.borders.get_filtered = borders_get_filtered
    fake_tests_db.ontology_entry.get_filtered = ontology_get_filtered
    monkeypatch.setattr(tests_service_module.calculator_service, "test_maslach_calculate_results", lambda results: [7])
    monkeypatch.setattr(tests_service_module, "GamificationService", DummyGamificationService)
    monkeypatch.setattr(tests_service_module, "recommendations", lambda payload: [])
    monkeypatch.setattr(tests_service_module, "load_data", lambda path: [])

    with pytest.raises(ScoreOutOfBoundsError):
        await TestService(fake_tests_db).save_result(
            tests_service_module.TestResultRequest.model_validate(build_test_result_request(results=[0, 1])),
            USER_ID,
        )


@pytest.mark.asyncio
async def test_service_get_test_result_by_user_and_test_returns_serialized_history(fake_tests_db):
    fake_tests_db.test_result.filtered_result = [make_test_result_row()]
    fake_tests_db.scale_result.filtered_result = [make_scale_result_row(score=7)]
    fake_tests_db.scales.one_result = make_scale()
    fake_tests_db.borders.filtered_result = [make_border(left_border=0, right_border=10, title="Norm")]

    result = await TestService(fake_tests_db).get_test_result_by_user_and_test(TEST_ID, USER_ID)

    assert result[0]["test_result_id"] == str(RESULT_ID)
    assert result[0]["scale_results"][0]["conclusion"] == "Norm"


@pytest.mark.asyncio
async def test_service_get_test_result_by_user_and_test_skips_missing_scale(fake_tests_db):
    fake_tests_db.test_result.filtered_result = [make_test_result_row()]
    fake_tests_db.scale_result.filtered_result = [make_scale_result_row(score=7)]
    fake_tests_db.scales.one_result = None

    result = await TestService(fake_tests_db).get_test_result_by_user_and_test(TEST_ID, USER_ID)

    assert result[0]["scale_results"] == []


@pytest.mark.asyncio
async def test_service_get_test_result_by_id_returns_serialized_payload(fake_tests_db):
    fake_tests_db.test_result.one_result = make_test_result_row()
    fake_tests_db.scale_result.filtered_result = [make_scale_result_row(score=7)]
    fake_tests_db.scales.one_result = make_scale()
    fake_tests_db.borders.filtered_result = [make_border(left_border=0, right_border=10, title="Norm")]

    result = await TestService(fake_tests_db).get_test_result_by_id(RESULT_ID)

    assert result["test_result_id"] == str(RESULT_ID)
    assert result["scale_results"][0]["score"] == 7


@pytest.mark.asyncio
async def test_service_get_test_result_by_id_should_raise_not_found_when_result_missing(fake_tests_db):
    with pytest.raises(ObjectNotFoundException):
        await TestService(fake_tests_db).get_test_result_by_id(RESULT_ID)


@pytest.mark.asyncio
async def test_service_get_passed_tests_by_user_returns_test_summaries(fake_tests_db):
    fake_tests_db.test_result.filtered_result = [
        make_test_result_row(result_id=RESULT_ID, test_id=TEST_ID, user_id=USER_ID),
        make_test_result_row(result_id=SECOND_RESULT_ID, test_id=SECOND_TEST_ID, user_id=USER_ID),
    ]
    fake_tests_db.tests.by_ids_result = [
        make_test(test_id=TEST_ID, title="Burnout Test"),
        make_test(test_id=SECOND_TEST_ID, title="Stress Test"),
    ]

    result = await TestService(fake_tests_db).get_passed_tests_by_user(USER_ID)

    assert [item["title"] for item in result] == ["Burnout Test", "Stress Test"]


@pytest.mark.asyncio
async def test_service_get_passed_tests_by_user_raises_not_found_when_tests_lookup_is_empty(fake_tests_db):
    fake_tests_db.test_result.filtered_result = [make_test_result_row(result_id=RESULT_ID, test_id=TEST_ID, user_id=USER_ID)]
    fake_tests_db.tests.by_ids_result = []

    with pytest.raises(ObjectNotFoundException):
        await TestService(fake_tests_db).get_passed_tests_by_user(USER_ID)


@pytest.mark.asyncio
async def test_service_get_passed_tests_by_user_raises_not_found_when_user_has_no_results(fake_tests_db):
    with pytest.raises(ObjectNotFoundException):
        await TestService(fake_tests_db).get_passed_tests_by_user(USER_ID)
