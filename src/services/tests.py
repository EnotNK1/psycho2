import datetime
import json
import uuid
import logging

from typing import Dict, Any, Optional

from fastapi import HTTPException
from fastapi import status
from src.models import AnswerChoiceOrm

from src.schemas.tests import TestAdd, ScaleAdd, BordersAdd, AnswerChoice, Question, TestResultRequest, \
    TestDetailsResponse, AnswerChoiceDetail, QuestionDetail, BorderDetail, ScaleDetail, ScaleResult, \
    TestSaveResult
from src.services.base import BaseService
from src.exceptions import (
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    MyAppException, InvalidAnswersCountError, ResultsScaleMismatchError, ScoreOutOfBoundsError,
)
from src.services.calculator import calculator_service
from src.services.inquiry import InquiryService

logger = logging.getLogger(__name__)


class TestService(BaseService):

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
                raise MyAppException()

    async def add_scales_and_borders(self, scales_data):
        scales = [ScaleAdd.model_validate(scale) for scale in scales_data]

        for scale in scales:
            try:
                # 1. Проверяем, что test_id указан
                if not scale.test_id:
                    logger.warning(f"Для шкалы '{scale.title}' не указан test_id. Пропускаем.")
                    continue

                # 2. Проверяем существование теста
                test = await self.db.tests.get_one_or_none(id=scale.test_id)
                if not test:
                    logger.warning(f"Тест с ID={scale.test_id} не найден. Пропускаем шкалу '{scale.title}'.")
                    continue

                # 3. Обработка шкалы (без изменений)
                existing_scale = await self.db.scales.get_one_or_none(id=scale.id)
                if existing_scale:
                    logger.info(f"Шкала с id={scale.id} уже существует. Пропускаем.")
                else:
                    await self.db.scales.add(scale)
                    logger.info(f"Шкала с id={scale.id} добавлена и связана с тестом {test.id}.")

                # 4. Обработка границ (измененная логика)
                borders_data = self.load_borders_for_scale(scale.id)
                borders = [BordersAdd.model_validate(border) for border in borders_data]

                for border in borders:
                    try:
                        # Сначала пытаемся удалить существующую границу (если есть)
                        await self.db.borders.delete(id=border.id)
                        logger.info(f"Старая граница {border.id} удалена.")

                        # Затем добавляем новую
                        await self.db.borders.add(border)
                        logger.info(f"Граница {border.id} для шкалы {scale.id} добавлена.")

                    except ObjectNotFoundException:
                        # Если границы не было - просто добавляем
                        await self.db.borders.add(border)
                        logger.info(f"Граница {border.id} для шкалы {scale.id} добавлена (не существовала ранее).")

                    except Exception as ex:
                        logger.error(f"Ошибка при обработке границы {border.id}: {ex}")
                        await self.db.rollback()
                        raise MyAppException()

            except ObjectAlreadyExistsException as ex:
                logger.info(f"Шкала с id={scale.id} уже существует. Пропускаем.")
            except Exception as ex:
                logger.error(f"Ошибка при добавлении шкалы: {ex}")
                await self.db.rollback()
                raise MyAppException()

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
                raise MyAppException()

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
                raise MyAppException()

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

            with open("services/info/inquiry.json", encoding="utf-8") as file:
                inquiry_data = json.load(file)
            await InquiryService(self.db).check_and_create_inquiries(inquiry_data)

            await self.db.commit()
            return {"status": "OK", "message": "Тесты, шкалы, границы, ответы и вопросы успешно созданы или пропущены"}

        except Exception as ex:
            logger.error(f"Ошибка при автоматическом создании данных: {ex}")
            await self.db.rollback()
            raise MyAppException()

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
            raise MyAppException()

    async def test_by_id(self, test_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        try:
            test = await self.db.tests.get_one(test_id)
            if not test:
                raise ObjectNotFoundException()
            return test
        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении теста: {ex}")
            raise MyAppException()

    async def test_questions(self, test_id: uuid.UUID) -> list[dict[str, Any]]:
        """
        Получает вопросы для теста по его ID.
        """
        try:
            # Получаем вопросы по test_id
            questions = await self.db.question.get_filtered(test_id=test_id)
            if not questions:
                raise ObjectNotFoundException()

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

        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении вопросов: {ex}")
            raise MyAppException()

    async def test_questions_with_answers(self, test_id: uuid.UUID) -> list[dict[str, Any]]:

        try:
            # Получаем вопросы по test_id
            questions = await self.db.question.get_filtered(test_id=test_id)
            if not questions:
                raise ObjectNotFoundException()

            # Собираем все ID ответов для всех вопросов
            all_answer_ids = []
            for question in questions:
                all_answer_ids.extend(question.answer_choice)

            # Получаем все ответы одним запросом
            answers = await self.db.answer_choice.get_by_ids(all_answer_ids)
            answer_dict = {answer.id: answer for answer in answers}

            # Формируем ответ
            result = []
            for question in questions:
                # Получаем ответы для текущего вопроса
                question_answers = []
                for answer_id in question.answer_choice:
                    answer = answer_dict.get(answer_id)
                    if answer:
                        question_answers.append({
                            "id": answer.id,
                            "text": answer.text,
                            "score": answer.score
                        })

                question_data = {
                    "id": question.id,
                    "text": question.text,
                    "number": question.number,
                    "test_id": question.test_id,
                    "answer_choices": question_answers
                }
                result.append(question_data)

            return result

        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении вопросов: {ex}")
            raise MyAppException()

    async def answers_by_question_id(self, test_id: uuid.UUID, question_id: uuid.UUID) -> list[AnswerChoiceOrm]:
        """
        Получает все ответы, связанные с вопросом по его ID, и проверяет, что вопрос принадлежит указанному тесту.
        """
        try:
            # Проверяем, существует ли тест
            test = await self.db.tests.get_one_or_none(id=test_id)
            if not test:
                raise ObjectNotFoundException()

            # Проверяем, существует ли вопрос и принадлежит ли он указанному тесту
            question = await self.db.question.get_one_or_none(id=question_id, test_id=test_id)
            if not question:
                raise ObjectNotFoundException()
            answers = []
            # Получаем ответы для вопроса
            for answer_id in question.answer_choice:
                answer = await self.db.answer_choice.get_filtered(id=answer_id)
                if answer:
                    answers.append(answer)
            if not answer:
                raise ObjectNotFoundException()

            return answers

        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении ответов: {ex}")
            raise MyAppException()

    async def details(self, test_id: uuid.UUID) -> TestDetailsResponse:
        logger.info(f"Получен запрос на детали теста с test_id={test_id}")
        try:
            # Получаем тест
            test = await self.db.tests.get_one(test_id)
            if not test:
                raise ObjectNotFoundException()

            # Получаем шкалы для теста
            scales = await self.db.scales.get_filtered(test_id=test_id)
            scale_details = []
            for scale in scales:
                # Получаем границы для каждой шкалы
                borders = await self.db.borders.get_filtered(scale_id=scale.id)
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
            questions = await self.db.question.get_filtered(test_id=test_id)
            question_details = []
            for question in questions:
                for answer in question.answer_choice:
                    answers = await self.db.answer_choice.get_filtered(id=answer)
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

        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении теста: {ex}")
            raise MyAppException()

    async def save_result(self, test_result_data: TestResultRequest, user_id: uuid.UUID):
        try:
            test = await self.db.tests.get_one(id=test_result_data.test_id)
            if not test:
                raise ObjectNotFoundException()

            questions = await self.db.question.get_filtered(test_id=test_result_data.test_id)
            if not questions:
                raise ObjectNotFoundException()

            expected_count = len(questions)
            received_count = len(test_result_data.results)
            if received_count != expected_count:
                raise InvalidAnswersCountError

            scales = await self.db.scales.get_filtered(test_id=test_result_data.test_id)
            if not scales:
                raise ObjectNotFoundException()

            calculation_methods = {
                "Определяем выгорание на работе": calculator_service.test_maslach_calculate_results,
                "Почему я себя так чувствую?": calculator_service.test_dass21_calculate_results,
                "Насколько мне тревожно?": calculator_service.test_stai_calculate_results,
                "Как я веду себя в стрессовых ситуациях?": calculator_service.test_coling_calculate_results,
                "Мешаю ли я себе?": calculator_service.test_cmq_calculate_results,
                "Есть ли у меня депрессия?": calculator_service.test_back_calculate_results,
                "Потеряли интерес к работе?": calculator_service.test_jas_calculate_results,
                "Стрессоустойчивость, это про меня?": calculator_service.test_stress_calculate_results,
            }

            calculate_method = calculation_methods.get(test.title)
            if not calculate_method:
                raise ObjectNotFoundException()

            scale_sum_list = calculate_method(test_result_data.results)
            logger.info(f"Рассчитанные результаты: {scale_sum_list}")

            if len(scale_sum_list) != len(scales):
                raise ResultsScaleMismatchError()

            try:
                test_res_id = uuid.uuid4()
                test_res = TestSaveResult(
                    id=test_res_id,
                    user_id=user_id,
                    test_id=test.id,
                    date=datetime.datetime.now()
                )
                await self.db.test_result.add(test_res)
                await self.db.session.flush()

                result = []
                for scale, score in zip(scales, scale_sum_list):
                    # Проверка границ значений
                    if score < scale.min or score > scale.max:
                        raise ScoreOutOfBoundsError()

                    borders = await self.db.borders.get_filtered(scale_id=scale.id)
                    if not borders:
                        raise ObjectNotFoundException()

                    scale_result = ScaleResult(
                        id=uuid.uuid4(),
                        score=score,
                        scale_id=scale.id,
                        test_result_id=test_res_id
                    )
                    await self.db.scale_result.add(scale_result)

                    for border in borders:
                        if border.left_border <= score <= border.right_border:
                            result.append({
                                "scale_id": str(scale.id),
                                "scale_title": scale.title,
                                "score": score,
                                "conclusion": border.title,
                                "color": border.color,
                                "user_recommendation": border.user_recommendation
                            })
                            break
                    else:
                        raise ObjectNotFoundException()

                await self.db.session.commit()
                return {
                    "test_result_id": str(test_res_id),
                    "result": result
                }

            except HTTPException:
                await self.db.session.rollback()
                raise
            except Exception as e:
                await self.db.session.rollback()
                logger.error(f"Ошибка сохранения: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка сохранения результатов"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Произошла непредвиденная ошибка"
            )

    async def get_test_result_by_user_and_test(
            self, test_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:

        try:
            # Получаем результат теста для указанного пользователя и теста
            test_result = await self.db.test_result.get_one_or_none(
                test_id=test_id, user_id=user_id
            )

            # Получаем результаты шкал для данного результата теста
            scale_results = await self.db.scale_result.get_filtered(test_result_id=test_result.id)

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
                scale = await self.db.scales.get_one(id=sr.scale_id)
                if not scale:
                    continue

                # Получаем границы для шкалы
                borders = await self.db.borders.get_filtered(scale_id=scale.id)

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

        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении результата теста: {ex}")
            raise MyAppException()

    async def get_test_result_by_id(self, result_id: uuid.UUID) -> Dict[str, Any]:
        """
        Получает результат теста по его ID.
        Возвращает результат в формате, соответствующем примеру выходных данных.
        """
        try:
            # Получаем результат теста по его ID
            test_result = await self.db.test_result.get_one(id=result_id)

            # Получаем результаты шкал для данного результата теста
            scale_results = await self.db.scale_result.get_filtered(test_result_id=test_result.id)

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
                scale = await self.db.scales.get_one(id=sr.scale_id)
                if not scale:
                    continue  # Пропускаем, если шкала не найдена

                # Получаем границы для шкалы
                borders = await self.db.borders.get_filtered(scale_id=scale.id)

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

        except ObjectNotFoundException:
            raise ObjectNotFoundException()
        except Exception as ex:
            logger.error(f"Ошибка при получении результата теста: {ex}")
            raise MyAppException()

    async def get_passed_tests_by_user(self, user_id: uuid.UUID) -> list[Dict[str, Any]]:
        try:
            # Получаем все результаты тестов для указанного пользователя
            test_results = await self.db.test_result.get_filtered(user_id=user_id)
            if not test_results:
                raise ObjectNotFoundException()

            test_ids = [str(tr.test_id) for tr in test_results]

            tests = await self.db.tests.get_by_ids(test_ids)
            if not tests:
                raise ObjectNotFoundException()

            test_dict = {str(test.id): test for test in tests}

            passed_tests = []
            for test_result in test_results:
                test = test_dict.get(str(test_result.test_id))
                if test:
                    passed_tests.append({
                        "title": test.title,
                        "description": test.description,
                        "test_id": str(test.id),
                        "link": test.link,
                    })

            return passed_tests

        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении пройденных тестов: {ex}")
            raise MyAppException()
