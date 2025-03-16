import json
import uuid
import logging
from fastapi import HTTPException
from sqlalchemy import select
from typing import Dict, Any, Optional

from sqlalchemy.orm import joinedload, selectinload

from src.models import TestOrm, ScaleOrm, BordersOrm, QuestionOrm, AnswerChoiceOrm, TestResultOrm, ScaleResultOrm
from src.repositories.answer_choices import AnswerChoiceRepository
from src.repositories.borders import BordersRepository
from src.repositories.questions import QuestionRepository
from src.repositories.scale import ScalesRepository
from src.repositories.scale_result import ScaleResultRepository
from src.repositories.test_result import TestResultRepository
from src.schemas.tests import TestAdd, ScaleAdd, BordersAdd, AnswerChoice, Question, TestResultRequest, \
    TestDetailsResponse, AnswerChoiceDetail, QuestionDetail, BorderDetail, ScaleDetail, Test, Scale
from src.services.base import BaseService
from src.exceptions import (
    ObjectNotFoundException,
    SeveralObjectsFoundException,
    ObjectAlreadyExistsException,
    ObjectNotFoundHTTPException,
    SeveralObjectsFoundHTTPException,
    UserEmailAlreadyExistsHTTPException,
    IncorrectPasswordHTTPException,
    NoAccessTokenHTTPException,
    EmailNotRegisteredHTTPException,
    PasswordDoNotMatchHTTPException, MyAppHTTPException,
)

logger = logging.getLogger(__name__)


class TestService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.session = db.session
        self.answer_choice_repo = AnswerChoiceRepository(db)
        self.test_result_repo = TestResultRepository(db)
        self.scale_result_repo = ScaleResultRepository(db)
        self.scale_repo = ScalesRepository(db)
        self.question_repo = QuestionRepository(db)
        self.borders_repo = BordersRepository(db)

    def load_borders_for_scale(self, scale_id: uuid.UUID) -> list[dict]:
        with open("services/info/borders_info.json", encoding="utf-8") as file:
            borders_data = json.load(file)

        filtered_borders = [border for border in borders_data if border["scale_id"] == str(scale_id)]

        return filtered_borders

    async def add_tests(self, tests_data):
        tests = [TestAdd.model_validate(test) for test in tests_data]
        for test in tests:
            try:
                existing_test = await self.db.tests.get_one_or_none(id=test.id)
                if existing_test:
                    logger.info(f"Тест с id={test.id} уже существует. Пропускаем.")
                else:
                    await self.db.tests.add(test)
                    logger.info(f"Тест с id={test.id} добавлен.")
            except ObjectAlreadyExistsException as ex:
                logger.info(f"Тест с id={test.id} уже существует. Пропускаем.")
            except Exception as ex:
                logger.error(f"Ошибка при добавлении теста: {ex}")
                await self.db.rollback()
                raise MyAppHTTPException(detail=f"Ошибка при добавлении теста: {ex}")

    async def add_scales_and_borders(self, scales_data):
        scales = [ScaleAdd.model_validate(scale) for scale in scales_data]
        for scale in scales:
            try:
                test = await self.db.tests.get_one_or_none(title=scale.title)
                if not test:
                    logger.warning(f"Тест для шкалы '{scale.title}' не найден. Пропускаем.")
                    continue

                scale.test_id = test.id

                existing_scale = await self.db.scales.get_one_or_none(id=scale.id)
                if existing_scale:
                    logger.info(f"Шкала с id={scale.id} уже существует. Пропускаем.")
                else:
                    await self.db.scales.add(scale)
                    logger.info(f"Шкала с id={scale.id} добавлена и связана с тестом {test.id}.")

                    borders_data = self.load_borders_for_scale(scale.id)
                    borders = [BordersAdd.model_validate(border) for border in borders_data]

                    for border in borders:
                        try:
                            await self.db.borders.add(border)
                            logger.info(f"Граница для шкалы {scale.id} добавлена.")
                        except ObjectAlreadyExistsException as ex:
                            logger.info(f"Граница для шкалы {scale.id} уже существует. Пропускаем.")
                        except Exception as ex:
                            logger.error(f"Ошибка при добавлении границы: {ex}")
                            await self.db.rollback()
                            raise MyAppHTTPException(detail=f"Ошибка при добавлении границы: {ex}")

            except ObjectAlreadyExistsException as ex:
                logger.info(f"Шкала с id={scale.id} уже существует. Пропускаем.")
            except Exception as ex:
                logger.error(f"Ошибка при добавлении шкалы: {ex}")
                await self.db.rollback()
                raise MyAppHTTPException(detail=f"Ошибка при добавлении шкалы: {ex}")

    async def add_answer_choices(self, answer_choices_data):
        answer_choices = [AnswerChoice.model_validate(answer) for answer in answer_choices_data]
        for answer in answer_choices:
            try:
                existing_answer = await self.db.answer_choice.get_one_or_none(id=answer.id)
                if existing_answer:
                    logger.info(f"Ответ с id={answer.id} уже существует. Пропускаем.")
                else:
                    await self.db.answer_choice.add(answer)
                    logger.info(f"Ответ с id={answer.id} добавлен.")
            except ObjectAlreadyExistsException as ex:
                logger.info(f"Ответ с id={answer.id} уже существует. Пропускаем.")
            except Exception as ex:
                logger.error(f"Ошибка при добавлении ответа: {ex}")
                await self.db.rollback()
                raise MyAppHTTPException(detail=f"Ошибка при добавлении ответа: {ex}")

    async def add_questions(self, questions_data):
        questions = [Question.model_validate(question) for question in questions_data]
        for question in questions:
            try:
                existing_question = await self.db.question.get_one_or_none(id=question.id)
                if existing_question:
                    logger.info(f"Вопрос с id={question.id} уже существует. Пропускаем.")
                else:
                    await self.db.question.add(question)
                    logger.info(f"Вопрос с id={question.id} добавлен.")
            except ObjectAlreadyExistsException as ex:
                logger.info(f"Вопрос с id={question.id} уже существует. Пропускаем.")
            except Exception as ex:
                logger.error(f"Ошибка при добавлении вопроса: {ex}")
                await self.db.rollback()
                raise MyAppHTTPException(detail=f"Ошибка при добавлении вопроса: {ex}")

    async def auto_create(self):
        try:
            with open("services/info/test_info.json", encoding="utf-8") as file:
                tests_data = json.load(file)
            await self.add_tests(tests_data)

            with open("services/info/scale_info.json", encoding="utf-8") as file:
                scales_data = json.load(file)
            await self.add_scales_and_borders(scales_data)

            with open("services/info/answer_choices_info.json", encoding="utf-8") as file:
                answer_choices_data = json.load(file)
            await self.add_answer_choices(answer_choices_data)

            with open("services/info/questions_info.json", encoding="utf-8") as file:
                questions_data = json.load(file)
            await self.add_questions(questions_data)

            await self.db.commit()
            return {"status": "OK", "message": "Тесты, шкалы, границы, ответы и вопросы успешно созданы или пропущены"}

        except Exception as ex:
            logger.error(f"Ошибка при автоматическом создании данных: {ex}")
            await self.db.rollback()
            raise MyAppHTTPException(detail=f"Ошибка при автоматическом создании данных: {ex}")

    async def all_tests(self) -> list[Dict[str, Any]]:
        try:
            # Получаем все тесты
            tests = await self.db.tests.get_all()
            result = []
            for test in tests:
                # Формируем данные для текущего теста
                test_data = {
                    "id": test.id,
                    "title": test.title,
                    "description": test.description,
                    "short_desc": test.short_desc,
                    "link": test.link
                }
                result.append(test_data)
            return result

        except Exception as ex:
            logger.error(f"Ошибка при получении списка тестов: {ex}")
            await self.db.rollback()
            raise MyAppHTTPException(detail=f"Ошибка при получении списка тестов: {ex}")

    async def test_by_id(self, test_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Получаем тест по его id
        """
        try:
            test = await self.db.tests.get_one(test_id)
            if not test:
                raise ObjectNotFoundHTTPException(detail="Тест не найден")
            return test
        except ObjectNotFoundHTTPException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении теста: {ex}")
            raise MyAppHTTPException(detail=f"Ошибка при получении теста: {ex}")

    async def test_questions(self, test_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Получает вопросы для теста по его ID.
        """
        try:
            # Получаем вопросы по test_id
            questions = await self.question_repo.all_by_test_id(test_id)
            if not questions:
                raise ObjectNotFoundHTTPException(detail="Вопросы для данного теста не найдены")

            # Формируем ответ
            result = []
            for question in questions:
                question_data = {
                    "id": question.id,
                    "text": question.text,
                    "number": question.number,
                    "test_id": question.test_id,
                    "answer_choice": question.answer_choice  # Список ID ответов
                }
                result.append(question_data)

            return result

        except ObjectNotFoundHTTPException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении вопросов: {ex}")
            raise MyAppHTTPException(detail=f"Ошибка при получении вопросов: {ex}")

    async def answers_by_question_id(self, test_id: uuid.UUID, question_id: uuid.UUID) -> list[AnswerChoiceOrm]:
        """
        Получает все ответы, связанные с вопросом по его ID, и проверяет, что вопрос принадлежит указанному тесту.
        """
        try:
            # Проверяем, существует ли тест
            test = await self.db.tests.get_one_or_none(id=test_id)
            if not test:
                raise ObjectNotFoundHTTPException(detail="Тест не найден")

            # Проверяем, существует ли вопрос и принадлежит ли он указанному тесту
            question = await self.question_repo.get_one_or_none(id=question_id, test_id=test_id)
            if not question:
                raise ObjectNotFoundHTTPException(detail="Вопрос не найден или не принадлежит указанному тесту")

            # Получаем ответы для вопроса
            answers = await self.answer_choice_repo.all_by_question_id(question_id)
            if not answers:
                raise ObjectNotFoundHTTPException(detail="Ответы для данного вопроса не найдены")

            return answers

        except ObjectNotFoundHTTPException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении ответов: {ex}")
            raise MyAppHTTPException(detail=f"Ошибка при получении ответов: {ex}")

    async def details(self, test_id: uuid.UUID) -> TestDetailsResponse:
        logger.info(f"Получен запрос на детали теста с test_id={test_id}")
        try:
            # Получаем тест
            test = await self.db.tests.get_one(test_id)
            if not test:
                raise ObjectNotFoundHTTPException(detail="Тест не найден")

            # Получаем шкалы для теста
            scales = await self.scale_repo.get_all_by_test_id(test_id)
            scale_details = []
            for scale in scales:
                # Получаем границы для каждой шкалы
                borders = await self.borders_repo.all_by_scale_id(scale.id)
                scale_details.append(ScaleDetail(
                    id=scale.id,
                    title=scale.title,
                    min=scale.min,
                    max=scale.max,
                    borders=[BorderDetail(
                        id=border.id,
                        left_border=border.left_border,
                        right_border=border.right_border,
                        color=border.color,
                        title=border.title,
                        user_recommendation=border.user_recommendation
                    ) for border in borders]
                ))

            # Получаем вопросы для теста
            questions = await self.question_repo.all_by_test_id(test_id)
            question_details = []
            for question in questions:
                # Получаем ответы для каждого вопроса
                answers = await self.answer_choice_repo.all_by_question_id(question.id)
                question_details.append(QuestionDetail(
                    id=question.id,
                    text=question.text,
                    number=question.number,
                    answers=[AnswerChoiceDetail(
                        id=answer.id,
                        text=answer.text,
                        score=answer.score
                    ) for answer in answers]
                ))

            # Формируем итоговый ответ
            return TestDetailsResponse(
                id=test.id,
                title=test.title,
                description=test.description,
                short_desc=test.short_desc,
                link=test.link,
                scales=scale_details,
                questions=question_details
            )

        except ObjectNotFoundHTTPException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении теста: {ex}")
            raise MyAppHTTPException(detail=f"Ошибка при получении теста: {ex}")

    async def save_result(self, test_result_data: TestResultRequest, user_id: uuid.UUID):
        try:
            # Преобразуем дату в offset-naive, если она offset-aware
            if test_result_data.date.tzinfo is not None:
                test_result_data.date = test_result_data.date.replace(tzinfo=None)

            # Создаем запись о результате теста
            test_result_id = uuid.uuid4()
            test_result = TestResultOrm(
                id=test_result_id,
                user_id=user_id,
                test_id=test_result_data.test_id,
                date=test_result_data.date  # Используем преобразованную дату
            )

            async with self.session.begin():  # This ensures the session is committed or rolled back
                self.session.add(test_result)

                # Получаем все шкалы для данного теста
                scales = await self.scale_repo.get_all_by_test_id(test_result_data.test_id)
                if not scales:
                    raise ObjectNotFoundHTTPException(detail="Шкалы для данного теста не найдены")

                # Сохраняем результаты для каждой шкалы
                for scale, result in zip(scales, test_result_data.results):
                    scale_result_id = uuid.uuid4()
                    scale_result = ScaleResultOrm(
                        id=scale_result_id,
                        score=result,
                        scale_id=scale.id,
                        test_result_id=test_result_id
                    )
                    self.session.add(scale_result)  # Убрали await, так как add не асинхронный

            # Коммитим изменения после завершения сессии
            await self.session.commit()
            return {"status": "OK", "message": "Результаты теста успешно сохранены"}

        except ObjectNotFoundHTTPException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при сохранении результатов теста: {ex}")
            raise MyAppHTTPException(detail=f"Ошибка при сохранении результатов теста: {ex}")

    async def get_test_result_by_user_and_test(
            self, test_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:

        try:
            # Получаем результат теста для указанного пользователя и теста
            test_result = await self.test_result_repo.get_one_or_none(
                test_id=test_id, user_id=user_id
            )
            if not test_result:
                raise ObjectNotFoundHTTPException(detail="Результат теста не найден")

            # Получаем результаты шкал для данного результата теста
            scale_results = await self.scale_result_repo.get_all_by_test_result_id(test_result.id)

            # Формируем ответ
            result = {
                "test_id": str(test_result.test_id),
                "test_result_id": str(test_result.id),
                "datetime": test_result.date.isoformat(),  # Преобразуем дату в строку в формате ISO
                "scale_results": [],
            }

            # Для каждого результата шкалы получаем дополнительные данные
            for sr in scale_results:
                # Получаем информацию о шкале
                scale = await self.scale_repo.get_one(id=sr.scale_id)
                if not scale:
                    continue  # Пропускаем, если шкала не найдена

                # Получаем границы для шкалы
                borders = await self.borders_repo.all_by_scale_id(scale.id)

                # Определяем вывод и рекомендации на основе score
                conclusion = ""
                color = ""
                user_recommendation = ""
                for border in borders:
                    if border.left_border <= sr.score <= border.right_border:
                        conclusion = border.title
                        color = border.color
                        user_recommendation = border.user_recommendation
                        break

                # Добавляем результат шкалы в ответ
                result["scale_results"].append({
                    "scale_id": str(scale.id),
                    "scale_title": scale.title,
                    "score": sr.score,
                    "max_score": scale.max,  # Максимальное значение шкалы
                    "conclusion": conclusion,
                    "color": color,
                    "user_recommendation": user_recommendation,
                })

            return result

        except ObjectNotFoundHTTPException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении результата теста: {ex}")
            raise MyAppHTTPException(detail=f"Ошибка при получении результата теста: {ex}")

    async def get_test_result_by_id(self, result_id: uuid.UUID) -> Dict[str, Any]:
        """
        Получает результат теста по его ID.
        Возвращает результат в формате, соответствующем примеру выходных данных.
        """
        try:
            # Получаем результат теста по его ID
            test_result = await self.test_result_repo.get_one(id=result_id)
            if not test_result:
                raise ObjectNotFoundHTTPException(detail="Результат теста не найден")

            # Получаем результаты шкал для данного результата теста
            scale_results = await self.scale_result_repo.get_all_by_test_result_id(test_result.id)

            # Формируем ответ
            result = {
                "test_id": str(test_result.test_id),
                "test_result_id": str(test_result.id),
                "datetime": test_result.date.isoformat(),  # Преобразуем дату в строку в формате ISO
                "scale_results": [],
            }

            # Для каждого результата шкалы получаем дополнительные данные
            for sr in scale_results:
                # Получаем информацию о шкале
                scale = await self.scale_repo.get_one(id=sr.scale_id)
                if not scale:
                    continue  # Пропускаем, если шкала не найдена

                # Получаем границы для шкалы
                borders = await self.borders_repo.all_by_scale_id(scale.id)

                # Определяем вывод и рекомендации на основе score
                conclusion = ""
                color = ""
                user_recommendation = ""
                for border in borders:
                    if border.left_border <= sr.score <= border.right_border:
                        conclusion = border.title
                        color = border.color
                        user_recommendation = border.user_recommendation
                        break

                # Добавляем результат шкалы в ответ
                result["scale_results"].append({
                    "scale_id": str(scale.id),
                    "scale_title": scale.title,
                    "score": sr.score,
                    "max_score": scale.max,  # Максимальное значение шкалы
                    "conclusion": conclusion,
                    "color": color,
                    "user_recommendation": user_recommendation,
                })

            return result

        except ObjectNotFoundHTTPException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении результата теста: {ex}")
            raise MyAppHTTPException(detail=f"Ошибка при получении результата теста: {ex}")

    async def get_passed_tests_by_user(self, user_id: uuid.UUID) -> list[Dict[str, Any]]:
        """
        Получает все пройденные тесты для указанного пользователя.
        Возвращает список тестов с их названиями, описаниями, ID и ссылками.
        """
        try:
            # Получаем все результаты тестов для указанного пользователя
            test_results = await self.test_result_repo.get_all_by_user_id(user_id)
            if not test_results:
                raise ObjectNotFoundHTTPException(detail="Пройденные тесты не найдены")

            # Формируем список пройденных тестов
            passed_tests = []
            for test_result in test_results:
                # Получаем информацию о тесте
                test = await self.db.tests.get_one(id=test_result.test_id)  # Используем test_id
                if not test:
                    continue  # Пропускаем, если тест не найден

                # Добавляем тест в список пройденных
                passed_tests.append({
                    "title": test.title,
                    "description": test.description,
                    "test_id": str(test.id),
                    "link": test.link,
                })

            return passed_tests

        except ObjectNotFoundHTTPException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении пройденных тестов: {ex}")
            raise MyAppHTTPException(detail=f"Ошибка при получении пройденных тестов: {ex}")
