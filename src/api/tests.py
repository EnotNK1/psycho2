import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Optional

from src.api.dependencies.db import DBDep
from src.api.dependencies.user_id import UserIdDep
from src.exceptions import ObjectNotFoundHTTPException, ObjectNotFoundException, MyAppException, MyAppHTTPException, \
    InternalErrorHTTPException, InvalidAnswersCountError, InvalidAnswersCountHTTPError, ResultsScaleMismatchError, \
    ResultsScaleMismatchHTTPError, ScoreOutOfBoundsError, ScoreOutOfBoundsHTTPError
from src.schemas.tests import TestResultRequest
from src.services.tests import TestService
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tests", tags=["Тесты"])
images_router = APIRouter(prefix="/images", tags=["Изображения"])


@router.post("/auto", summary="Автоматическое создание всех тестов")
async def auto_create(
        db: DBDep,
        user_id: UserIdDep
):
    await TestService(db).auto_create()
    return {"status": "OK"}


@router.get("",
            description="""
    Возвращает список всех доступных тестов в системе.
    Каждый тест содержит базовую информацию: ID, title, description, short_desc и link(ссылка на картинку).
    """,
            summary="Получение всех тестов")
async def all_tests(
        db: DBDep
):
    tests = await TestService(db).all_tests()
    return tests


@router.get("/{test_id}",
            description="""
    Возвращает детальную информацию о конкретном тесте по его идентификатору.\n
    Входные параметры: test_id.
    Cодержит cледующее: 
    {
        title: "string", 
        description: "string", 
        link(ссылка на картинку), 
        id(id теста), 
        short_desc: "string", 
        scale": [
            {
                "id": "ebe230f9-ea6c-4534-9e0d-32a6ea14027f",
                "max": (значение правой границы),
                "title": "Эмоциональное истощение",
                "min": 0,
                "test_id": "c9386cd7-4f63-4cbb-af35-54829ef9c14b",
                "borders": [
                    {
                        "id": "edb2b820-38b8-4b01-8d0b-4d9504e8242f",
                        "right_border": 15,
                        "title": "Норма",
                        "scale_id": "ebe230f9-ea6c-4534-9e0d-32a6ea14027f",
                        "color": "#015641",
                        "left_border": 0,
                        "user_recommendation": "string".
                    }
                ]
            }
        ]
    }
    """,
            summary="Получение теста по id")
async def test_by_id(
        test_id: uuid.UUID,
        db: DBDep
):
    try:
        return await TestService(db).test_by_id(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get("/{test_id}/questions",
            description="""
    Возвращает список всех вопросов для указанного теста.\n
    Входные параметры: test_id.
    Содержит следующее:
    [
        {
            "id": "52d2bcc0-507b-45ab-a2b0-18288e762670",
            "text": "Я чувствую себя эмоционально опустошенным.",
            "number": 1,
            "test_id": "c9386cd7-4f63-4cbb-af35-54829ef9c14b",
            "answer_choice": [
                "c492b2d1-b971-4316-8003-bb0d414bb76d",
                "b1fc6b9c-cee2-488b-9bd4-0c73a5cce1fa",
                "5ea97c90-47b0-498d-85f0-b05f5fae9c15",
                "6b002714-596c-40bb-97df-fc934c7f99ba",
                "d575bd4a-d197-4447-b615-ce9119e5c54e",
                "ec3ee878-2213-4a70-b095-85f9da50eae7",
                "35c0f8c7-a9c5-48c5-8356-35c679bbbc7c"
            ]
        }
    ]
    """,
            summary="Получение вопросов по test_id")
async def questions(
        test_id: uuid.UUID,
        db: DBDep
):
    try:
        test_service = TestService(db)
        return await test_service.test_questions(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get("/{test_id}/questions/answers",
            description="""
    Возвращает список всех вопросов с ответами для указанного теста.\n
    Входные параметры: test_id.
    Содержит следующее:.
    [
        {
            "id": "52d2bcc0-507b-45ab-a2b0-18288e762670",
            "text": "Я чувствую себя эмоционально опустошенным.",
            "number": 1,
            "test_id": "c9386cd7-4f63-4cbb-af35-54829ef9c14b",
            "answer_choice": [
                {
                    "id": "c492b2d1-b971-4316-8003-bb0d414bb76d",
                    "text": "Никогда",
                    "score": 0
                },
                {
                    "id": "6b002714-596c-40bb-97df-fc934c7f99ba",
                    "text": "Иногда",
                    "score": 3
                }
            ]
        }
    ]
    """,
            summary="Получение вопросов по test_id c ответами")
async def questions_with_answers(
        test_id: uuid.UUID,
        db: DBDep
):
    try:
        test_service = TestService(db)
        return await test_service.test_questions_with_answers(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get("/{test_id}/questions/{question_id}/answers/",
            description="""
    Возвращает все ответы для определенного вопроса.\n
    Входные параметры: test_id; question_id.
    Содержит следующее:.
    [
        [
            {
                "id": "c492b2d1-b971-4316-8003-bb0d414bb76d",
                "text": "Никогда",
                "score": 0
            }
        ],
        [
            {
                "id": "b1fc6b9c-cee2-488b-9bd4-0c73a5cce1fa",
                "text": "Очень редко",
                "score": 1
            }
        ]
    ]
    """,
            summary="Получение ответов по test_id и question_id")
async def answers_by_question_id(
        test_id: uuid.UUID,
        question_id: uuid.UUID,
        db: DBDep
):
    try:
        return await TestService(db).answers_by_question_id(test_id, question_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get("/{test_id}/details",
            description="""
    Возвращает все данные для определенного теста.\n
    Входные параметры: test_id.
    """,
            summary="Получение теста со всеми связанными данными")
async def details(
        test_id: uuid.UUID,  # FastAPI автоматически парсит строку в UUID
        db: DBDep
):
    try:
        test_service = TestService(db)
        return await test_service.details(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.post("/result",
             description="""
             Сохранение результата теста.\n
             Входящие данные:
             {
                "test_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "date": "2025-09-22T06:59:59.305Z",
                "results": [
                    1, 2, 1, 3, 4 (Пример сохранения теста с 5 вопросами)
                ]
             }
             
             В results записываются цифры (Значения score из запроса /tests/{test_id}/questions/answers) через запятую.
             1) Количество элементов в массиве должно точно соответствовать количеству вопросов в тесте
             2) Порядок элементов должен соответствовать порядку вопросов в тесте (от первого к последнему)
             3) Значения scores должны быть валидными баллами из вариантов ответов для каждого вопроса
            
    
             """,
             summary="Сохранение результата теста")
async def save_result(
        test_result_data: TestResultRequest,
        db: DBDep,
        user_id: UserIdDep,
):
    try:
        return await TestService(db).save_result(test_result_data, user_id)
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


@router.get("/{test_id}/results/",
            description="""
    Возвращает результат по test_id и user_id.\n
    Входные параметры: test_id; user_id.
    """,
            summary="Получение результата теста по test_id и user_id")
async def result_by_user_and_test(
        db: DBDep,
        current_user_id: UserIdDep,
        test_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
):
    try:
        test_service = TestService(db)
        target_user_id = user_id if user_id else current_user_id
        return await test_service.get_test_result_by_user_and_test(test_id, target_user_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get("/test_result/{result_id}",
            description="""
    Возвращает результат по result_id.\n
    Входные параметры: result_id.
    """,
            summary="Получение результата теста по его ID")
async def get_test_result_by_id(
        result_id: uuid.UUID,  # test_result_id передается как часть пути
        db: DBDep
):
    try:
        return await TestService(db).get_test_result_by_id(result_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get("/passed/user/{user_id}",
            description="""
    Возвращает все пройденные тесты по user_id.\n
    Входные параметры: user_id.
    Содержит следующее:
    [
        {
            "title": "Определяем выгорание на работе",
            "description": "Вы сможете разобраться в причинах профессионального выгорания: есть ли хроническая усталость и оторванность от мира.",
            "test_id": "c9386cd7-4f63-4cbb-af35-54829ef9c14b",
            "link": "/images/images_test/Оценка_выгорания_на_работе.png"
        }
    ]
    """,
            summary="Получение всех пройденных тестов для пользователя")
async def get_passed_tests_by_user(
        user_id: uuid.UUID,  # user_id передается как часть пути
        db: DBDep
):
    try:
        return await TestService(db).get_passed_tests_by_user(user_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get("/passed/user",
            description="""
    Возвращает все пройденные тесты для текущего пользователя.\n
    Содержит следующее:
    [
        {
            "title": "Определяем выгорание на работе",
            "description": "Вы сможете разобраться в причинах профессионального выгорания: есть ли хроническая усталость и оторванность от мира.",
            "test_id": "c9386cd7-4f63-4cbb-af35-54829ef9c14b",
            "link": "/images/images_test/Оценка_выгорания_на_работе.png"
        }
    ]
    """,
            summary="Получение всех пройденных тестов для текущего пользователя")
async def get_passed_tests(
        user_id: UserIdDep,  # Извлекаем user_id из токена
        db: DBDep
):
    return await TestService(db).get_passed_tests_by_user(user_id)


@images_router.get("/{file_path:path}", summary="Получение изображения по пути, пример images/img_1.png")
async def get_image(file_path: str):
    # Получаем абсолютный путь к директории images
    base_dir = Path(__file__).parent.parent  # Остаёмся в директории src
    images_dir = base_dir / "images"

    # Полный путь к файлу
    image_path = images_dir / file_path

    # Логирование для отладки
    logging.info(f"Requested file path: {file_path}")
    logging.info(f"Full image path: {image_path}")

    # Проверка, существует ли файл
    if not image_path.is_file():
        logging.error(f"Image not found: {image_path}")
        raise HTTPException(status_code=404, detail="Изображение не найдено")

    # Возвращаем файл как ответ
    return FileResponse(image_path)
