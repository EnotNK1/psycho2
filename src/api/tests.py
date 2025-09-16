import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
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


@router.get("", summary="Получение всех тестов")
async def all_tests(
        db: DBDep
):
    tests = await TestService(db).all_tests()
    return tests


@router.get("/{test_id}", summary="Получение теста по id")
async def test_by_id(
        test_id: uuid.UUID,
        db: DBDep
):
    try:
        return await TestService(db).test_by_id(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get("/{test_id}/questions", summary="Получение вопросов по test_id")
async def questions(
        test_id: uuid.UUID,
        db: DBDep
):
    try:
        test_service = TestService(db)
        return await test_service.test_questions(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException

@router.get("/{test_id}/questions/answers", summary="Получение вопросов по test_id c ответами")
async def questions_with_answers(
        test_id: uuid.UUID,
        db: DBDep
):
    try:
        test_service = TestService(db)
        return await test_service.test_questions_with_answers(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException

@router.get("/{test_id}/questions/{question_id}/answers/", summary="Получение ответов по test_id и question_id")
async def answers_by_question_id(
        test_id: uuid.UUID,
        question_id: uuid.UUID,
        db: DBDep
):
    try:
        return await TestService(db).answers_by_question_id(test_id, question_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException

@router.get("/{test_id}/details", summary="Получение теста со всеми связанными данными")
async def details(
        test_id: uuid.UUID,  # FastAPI автоматически парсит строку в UUID
        db: DBDep
):
    try:
        test_service = TestService(db)
        return await test_service.details(test_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.post("/result", summary="Сохранение результата теста")
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


@router.get("/{test_id}/results/{user_id}", summary="Получение результата теста по test_id и user_id")
async def result_by_user_and_test(
        test_id: uuid.UUID,
        user_id: uuid.UUID,
        db: DBDep,
):
    try:
        test_service = TestService(db)
        return await test_service.get_test_result_by_user_and_test(test_id, user_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException

@router.get("/test_result/{result_id}", summary="Получение результата теста по его ID")
async def get_test_result_by_id(
        result_id: uuid.UUID,  # test_result_id передается как часть пути
        db: DBDep
):
    try:
        return await TestService(db).get_test_result_by_id(result_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException

@router.get("/passed/user/{user_id}", summary="Получение всех пройденных тестов для пользователя")
async def get_passed_tests_by_user(
        user_id: uuid.UUID,  # user_id передается как часть пути
        db: DBDep
):
    try:
        return await TestService(db).get_passed_tests_by_user(user_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException

@router.get("/passed/user", summary="Получение всех пройденных тестов для текущего пользователя")
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
