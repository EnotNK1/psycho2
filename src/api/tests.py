from src.api.dependencies.access import require_client_access
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict, Any
from src.utils.data import load_data
from src.api.dependencies.db import DBDep
from src.api.dependencies.admin import verify_admin
from src.api.dependencies.user_id import UserIdDep
from src.exceptions import (
    ObjectNotFoundHTTPException,
    ObjectNotFoundException,
    MyAppException,
    MyAppHTTPException,
    InvalidAnswersCountError,
    InvalidAnswersCountHTTPError,
    ResultsScaleMismatchError,
    ResultsScaleMismatchHTTPError,
    ScoreOutOfBoundsError,
    ScoreOutOfBoundsHTTPError,
)
from src.schemas.tests import (
    AnswerChoiceCreate,
    AnswerChoiceResponse,
    AnswerChoiceUpdate,
    BorderCreate,
    BorderResponse,
    BordersUpdate,
    QuestionCreate,
    QuestionResponse,
    QuestionUpdate,
    ScaleCreate,
    ScaleResponse,
    ScaleUpdate,
    TestCreate,
    TestResponse,
    TestResultRequest,
    TestUpdate,
)
from src.services.tests import TestService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tests", tags=["Тесты"])
images_router = APIRouter(prefix="/images", tags=["Изображения"])


def _normalize_user_id(user_id: uuid.UUID | str) -> uuid.UUID:
    if isinstance(user_id, uuid.UUID):
        return user_id
    return uuid.UUID(str(user_id))


@router.post("/auto", summary="Автоматическое создание всех тестов")
async def auto_create(db: DBDep, admin_id: uuid.UUID = Depends(verify_admin)):
    await TestService(db).auto_create()
    return {"status": "OK"}


@router.post("/update-images", summary="Обновить изображения тестов")
async def update_test_images(db: DBDep, admin_id: uuid.UUID = Depends(verify_admin)):
    try:
        await TestService(db).update_test_links_from_file()
        return {"status": "OK", "message": "Изображения тестов обновлены"}
    except ObjectNotFoundException as e:
        raise ObjectNotFoundHTTPException(detail=str(e))


@router.post("/", response_model=TestResponse)
async def create_test(
    test_data: TestCreate, db: DBDep, admin_id: uuid.UUID = Depends(verify_admin)
):
    return await TestService(db).create_test(test_data)


@router.patch("/{test_id}", response_model=TestResponse)
async def update_test(
    test_id: uuid.UUID,
    test_data: TestUpdate,
    db: DBDep,
    admin_id: uuid.UUID = Depends(verify_admin),
):
    try:
        return await TestService(db).update_test(test_id, test_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.delete("/{test_id}", status_code=204)
async def delete_test(
    test_id: uuid.UUID, db: DBDep, admin_id: uuid.UUID = Depends(verify_admin)
):
    try:
        await TestService(db).delete_test(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.post("/{test_id}/scales", response_model=ScaleResponse)
async def create_scale(
    test_id: uuid.UUID,
    scale_data: ScaleCreate,
    db: DBDep,
    admin_id: uuid.UUID = Depends(verify_admin),
):
    try:
        return await TestService(db).create_scale(test_id, scale_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.patch("/scales/{scale_id}", response_model=ScaleResponse)
async def update_scale(
    scale_id: uuid.UUID,
    scale_data: ScaleUpdate,
    db: DBDep,
    admin_id: uuid.UUID = Depends(verify_admin),
):
    try:
        return await TestService(db).update_scale(scale_id, scale_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.delete("/scales/{scale_id}", status_code=204)
async def delete_scale(
    scale_id: uuid.UUID, db: DBDep, admin_id: uuid.UUID = Depends(verify_admin)
):
    try:
        await TestService(db).delete_scale(scale_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.post("/scales/{scale_id}/borders", response_model=BorderResponse)
async def create_border(
    scale_id: uuid.UUID,
    border_data: BorderCreate,
    db: DBDep,
    admin_id: uuid.UUID = Depends(verify_admin),
):
    try:
        return await TestService(db).create_border(scale_id, border_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.patch("/borders/{border_id}", response_model=BorderResponse)
async def update_border(
    border_id: uuid.UUID,
    border_data: BordersUpdate,
    db: DBDep,
    admin_id: uuid.UUID = Depends(verify_admin),
):
    try:
        return await TestService(db).update_border(border_id, border_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.delete("/borders/{border_id}", status_code=204)
async def delete_border(
    border_id: uuid.UUID, db: DBDep, admin_id: uuid.UUID = Depends(verify_admin)
):
    try:
        await TestService(db).delete_border(border_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.post("/{test_id}/questions", response_model=QuestionResponse)
async def create_question(
    test_id: uuid.UUID,
    question_data: QuestionCreate,
    db: DBDep,
    admin_id: uuid.UUID = Depends(verify_admin),
):
    try:
        return await TestService(db).create_question(test_id, question_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.patch("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: uuid.UUID,
    question_data: QuestionUpdate,
    db: DBDep,
    admin_id: uuid.UUID = Depends(verify_admin),
):
    try:
        return await TestService(db).update_question(question_id, question_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.delete("/questions/{question_id}", status_code=204)
async def delete_question(
    question_id: uuid.UUID, db: DBDep, admin_id: uuid.UUID = Depends(verify_admin)
):
    try:
        await TestService(db).delete_question(question_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.post("/answers", response_model=AnswerChoiceResponse)
async def create_answer_choice(
    answer_data: AnswerChoiceCreate,
    db: DBDep,
    admin_id: uuid.UUID = Depends(verify_admin),
):
    return await TestService(db).create_answer_choice(answer_data)


@router.patch("/answers/{answer_id}", response_model=AnswerChoiceResponse)
async def update_answer_choice(
    answer_id: uuid.UUID,
    answer_data: AnswerChoiceUpdate,
    db: DBDep,
    admin_id: uuid.UUID = Depends(verify_admin),
):
    try:
        return await TestService(db).update_answer_choice(answer_id, answer_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.delete("/answers/{answer_id}", status_code=204)
async def delete_answer_choice(
    answer_id: uuid.UUID, db: DBDep, admin_id: uuid.UUID = Depends(verify_admin)
):
    try:
        await TestService(db).delete_answer_choice(answer_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get(
    "",
    description="\n    Возвращает список всех доступных тестов в системе.\n    Каждый тест содержит базовую информацию: ID, title, description, short_desc и link(ссылка на картинку).\n    ",
    summary="Получение всех тестов",
)
async def all_tests(db: DBDep):
    tests = await TestService(db).all_tests()
    return tests


@router.get(
    "/{test_id}",
    description='\n    Возвращает детальную информацию о конкретном тесте по его идентификатору.\n\n    Входные параметры: test_id.\n    Cодержит cледующее: \n    {\n        title: "string", \n        description: "string", \n        link(ссылка на картинку), \n        id(id теста), \n        short_desc: "string", \n        scale": [\n            {\n                "id": "ebe230f9-ea6c-4534-9e0d-32a6ea14027f",\n                "max": (значение правой границы),\n                "title": "Эмоциональное истощение",\n                "min": 0,\n                "test_id": "c9386cd7-4f63-4cbb-af35-54829ef9c14b",\n                "borders": [\n                    {\n                        "id": "edb2b820-38b8-4b01-8d0b-4d9504e8242f",\n                        "right_border": 15,\n                        "title": "Норма",\n                        "scale_id": "ebe230f9-ea6c-4534-9e0d-32a6ea14027f",\n                        "color": "#015641",\n                        "left_border": 0,\n                        "user_recommendation": "string".\n                    }\n                ]\n            }\n        ]\n    }\n    ',
    summary="Получение теста по id",
)
async def test_by_id(test_id: uuid.UUID, db: DBDep):
    try:
        return await TestService(db).test_by_id(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get(
    "/{test_id}/questions",
    description='\n    Возвращает список всех вопросов для указанного теста.\n\n    Входные параметры: test_id.\n    Содержит следующее:\n    [\n        {\n            "id": "52d2bcc0-507b-45ab-a2b0-18288e762670",\n            "text": "Я чувствую себя эмоционально опустошенным.",\n            "number": 1,\n            "test_id": "c9386cd7-4f63-4cbb-af35-54829ef9c14b",\n            "answer_choice": [\n                "c492b2d1-b971-4316-8003-bb0d414bb76d",\n                "b1fc6b9c-cee2-488b-9bd4-0c73a5cce1fa",\n                "5ea97c90-47b0-498d-85f0-b05f5fae9c15",\n                "6b002714-596c-40bb-97df-fc934c7f99ba",\n                "d575bd4a-d197-4447-b615-ce9119e5c54e",\n                "ec3ee878-2213-4a70-b095-85f9da50eae7",\n                "35c0f8c7-a9c5-48c5-8356-35c679bbbc7c"\n            ]\n        }\n    ]\n    ',
    summary="Получение вопросов по test_id",
)
async def questions(test_id: uuid.UUID, db: DBDep):
    try:
        test_service = TestService(db)
        return await test_service.test_questions(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get(
    "/{test_id}/questions/answers",
    description='\n    Возвращает список всех вопросов с ответами для указанного теста.\n\n    Входные параметры: test_id.\n    Содержит следующее:.\n    [\n        {\n            "id": "52d2bcc0-507b-45ab-a2b0-18288e762670",\n            "text": "Я чувствую себя эмоционально опустошенным.",\n            "number": 1,\n            "test_id": "c9386cd7-4f63-4cbb-af35-54829ef9c14b",\n            "answer_choice": [\n                {\n                    "id": "c492b2d1-b971-4316-8003-bb0d414bb76d",\n                    "text": "Никогда",\n                    "score": 0\n                },\n                {\n                    "id": "6b002714-596c-40bb-97df-fc934c7f99ba",\n                    "text": "Иногда",\n                    "score": 3\n                }\n            ]\n        }\n    ]\n    ',
    summary="Получение вопросов по test_id c ответами",
)
async def questions_with_answers(test_id: uuid.UUID, db: DBDep):
    try:
        test_service = TestService(db)
        return await test_service.test_questions_with_answers(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get(
    "/{test_id}/questions/{question_id}/answers/",
    description='\n    Возвращает все ответы для определенного вопроса.\n\n    Входные параметры: test_id; question_id.\n    Содержит следующее:.\n    [\n        [\n            {\n                "id": "c492b2d1-b971-4316-8003-bb0d414bb76d",\n                "text": "Никогда",\n                "score": 0\n            }\n        ],\n        [\n            {\n                "id": "b1fc6b9c-cee2-488b-9bd4-0c73a5cce1fa",\n                "text": "Очень редко",\n                "score": 1\n            }\n        ]\n    ]\n    ',
    summary="Получение ответов по test_id и question_id",
)
async def answers_by_question_id(test_id: uuid.UUID, question_id: uuid.UUID, db: DBDep):
    try:
        return await TestService(db).answers_by_question_id(test_id, question_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get(
    "/{test_id}/details",
    description="\n    Возвращает все данные для определенного теста.\n\n    Входные параметры: test_id.\n    ",
    summary="Получение теста со всеми связанными данными",
)
async def details(test_id: uuid.UUID, db: DBDep):
    try:
        test_service = TestService(db)
        return await test_service.details(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


tests_info = load_data("src/services/info/test_info.json")


def should_add_relax(test_id: str, scales: List[Dict[str, Any]]) -> bool:
    """
    Определяет, нужно ли добавить "relax" в зависимости от test_id и результатов шкал.
    """
    if test_id == "bc9f1204-ea5d-40b0-b367-359bf9b2cc21":
        anxiety = next(
            (s for s in scales if "тревог" in s["scale_title"].lower()), None
        )
        stress = next((s for s in scales if "стресс" in s["scale_title"].lower()), None)
        return (anxiety and anxiety["score"] >= 1) and (stress and stress["score"] >= 3)
    elif test_id == "3a9a3c8d-348e-4f0d-aefd-0feaa960ac25":
        return any((s["score"] > 30 for s in scales))
    elif test_id == "c9386cd7-4f63-4cbb-af35-54829ef9c14b":
        em_exhaustion = next(
            (
                s
                for s in scales
                if "эмоциональное истощение" in s["scale_title"].lower()
            ),
            None,
        )
        depersonalization = next(
            (s for s in scales if "деперсонализация" in s["scale_title"].lower()), None
        )
        return (em_exhaustion and em_exhaustion["score"] > 15) and (
            depersonalization and depersonalization["score"] > 6
        )
    elif test_id == "f56b5284-323e-42db-bd74-c80e8a5dc29a":
        perceived_stress = next(
            (
                s
                for s in scales
                if "воспринимаемого стресса" in s["scale_title"].lower()
                or "стресс" in s["scale_title"].lower()
            ),
            None,
        )
        return perceived_stress and perceived_stress["score"] > 13
    elif test_id == "ea869ca2-4e8f-4a98-8b13-4fbeedf30539":
        return any((s.get("conclusion") in ["Средний", "Высокий"] for s in scales))
    return False


@router.post(
    "/result",
    description='\n             Сохранение результата теста.\n\n             Входящие данные:\n             {\n                "test_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",\n                "date": "2025-09-22T06:59:59.305Z",\n                "results": [\n                    1, 2, 1, 3, 4 (Пример сохранения теста с 5 вопросами)\n                ]\n             }\n             \n             В results записываются цифры (Значения score из запроса /tests/{test_id}/questions/answers) через запятую.\n             1) Количество элементов в массиве должно точно соответствовать количеству вопросов в тесте\n             2) Порядок элементов должен соответствовать порядку вопросов в тесте (от первого к последнему)\n             3) Значения scores должны быть валидными баллами из вариантов ответов для каждого вопроса\n            \n    \n             ',
    summary="Сохранение результата теста",
)
async def save_result(
    test_result_data: TestResultRequest, db: DBDep, user_id: UserIdDep
):
    try:
        res = await TestService(db).save_result(test_result_data, user_id)
        test_id = str(test_result_data.test_id)
        if test_id:
            add_relax = should_add_relax(test_id, res["result"])
            res["tags"] = ["relax"] if add_relax else []
        else:
            res["tags"] = []
        return res
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except InvalidAnswersCountError:
        raise InvalidAnswersCountHTTPError
    except ResultsScaleMismatchError:
        raise ResultsScaleMismatchHTTPError
    except ScoreOutOfBoundsError:
        raise ScoreOutOfBoundsHTTPError
    except MyAppException:
        raise MyAppHTTPException


@router.get(
    "/{test_id}/results/",
    description="\n    Возвращает результат по test_id и user_id.\n\n    Входные параметры: test_id; user_id.\n    ",
    summary="Получение результата теста по test_id и user_id",
)
async def result_by_user_and_test(
    db: DBDep,
    current_user_id: UserIdDep,
    test_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
):
    await require_client_access(db, current_user_id, user_id or current_user_id)
    try:
        test_service = TestService(db)
        target_user_id = user_id if user_id else current_user_id
        res = await test_service.get_test_result_by_user_and_test_not_psyc(
            test_id, target_user_id
        )
        test_id_str = str(test_id)
        for item in res:
            scales = item.get("scale_results", [])
            add_relax = should_add_relax(test_id_str, scales)
            item["tags"] = ["relax"] if add_relax else []
        return res
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get(
    "/test_result/{result_id}",
    description="\n    Возвращает результат по result_id.\n\n    Входные параметры: result_id.\n    ",
    summary="Получение результата теста по его ID",
)
async def get_test_result_by_id(result_id: uuid.UUID, user_id: UserIdDep, db: DBDep):
    try:
        res = await TestService(db).get_test_result_by_id(
            result_id, _normalize_user_id(user_id)
        )
        test_id = res.get("test_id")
        scale_results = res.get("scale_results", [])
        if test_id:
            add_relax = should_add_relax(str(test_id), scale_results)
            res["tags"] = ["relax"] if add_relax else []
        else:
            res["tags"] = []
        return res
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get(
    "/passed/user/{user_id}",
    description='\n    Возвращает все пройденные тесты по user_id.\n\n    Каждый test_id возвращается один раз независимо от числа прохождений.\n    Все прохождения с датами доступны через /tests/{test_id}/results/.\n    Входные параметры: user_id.\n    Содержит следующее:\n    [\n        {\n            "title": "Определяем выгорание на работе",\n            "description": "Вы сможете разобраться в причинах профессионального выгорания: есть ли хроническая усталость и оторванность от мира.",\n            "test_id": "c9386cd7-4f63-4cbb-af35-54829ef9c14b",\n            "link": "/images/images_test/Оценка_выгорания_на_работе.png"\n        }\n    ]\n    ',
    summary="Получение всех пройденных тестов для пользователя",
)
async def get_passed_tests_by_user(
    user_id: uuid.UUID, db: DBDep, current_user_id: UserIdDep
):
    await require_client_access(db, current_user_id, user_id)
    try:
        return await TestService(db).get_passed_tests_by_user(user_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get(
    "/passed/user",
    description='\n    Возвращает все пройденные тесты для текущего пользователя.\n\n    Каждый test_id возвращается один раз независимо от числа прохождений.\n    Все прохождения с датами доступны через /tests/{test_id}/results/.\n    Содержит следующее:\n    [\n        {\n            "title": "Определяем выгорание на работе",\n            "description": "Вы сможете разобраться в причинах профессионального выгорания: есть ли хроническая усталость и оторванность от мира.",\n            "test_id": "c9386cd7-4f63-4cbb-af35-54829ef9c14b",\n            "link": "/images/images_test/Оценка_выгорания_на_работе.png"\n        }\n    ]\n    ',
    summary="Получение всех пройденных тестов для текущего пользователя",
)
async def get_passed_tests(user_id: UserIdDep, db: DBDep):
    try:
        return await TestService(db).get_passed_tests_by_user(user_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
