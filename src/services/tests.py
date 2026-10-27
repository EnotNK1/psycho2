from src.utils.data import data_path
import datetime
import json
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException
from fastapi import status
from src.models import AnswerChoiceOrm, TestOrm
from src.utils.data import load_data
from sqlalchemy import update
from src.schemas.tests import (
    TestAdd,
    ScaleAdd,
    BordersAdd,
    AnswerChoice,
    Question,
    TestResultRequest,
    TestDetailsResponse,
    AnswerChoiceDetail,
    QuestionDetail,
    BorderDetail,
    ScaleDetail,
    ScaleResult,
    TestSaveResult,
    TestCreate,
    TestUpdate,
    TestResponse,
    ScaleResponse,
    ScaleUpdate,
    ScaleCreate,
    BorderResponse,
    BorderCreate,
    BordersUpdate,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    AnswerChoiceCreate,
    AnswerChoiceUpdate,
    AnswerChoiceResponse,
)
from src.services.base import BaseService
from src.exceptions import (
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    MyAppException,
    InvalidAnswersCountError,
    ResultsScaleMismatchError,
    ScoreOutOfBoundsError,
)
from src.services.calculator import calculator_service

logger = logging.getLogger(__name__)


class TestService(BaseService):
    def _load_info_data(self, path: str) -> list[dict]:
        try:
            return load_data(path)
        except FileNotFoundError:
            logger.warning("Info file %s not found, using empty list", path)
            return []

    async def update_test_links_from_file(
        self, file_path: str = "src/services/info/test_info.json"
    ):
        with open(data_path(file_path), encoding="utf-8") as f:
            tests_data = json.load(f)
        for item in tests_data:
            test_id = item["id"]
            new_link = item.get("link", "")
            test = await self.db.tests.get_one(id=test_id)
            if not test:
                raise ObjectNotFoundException(f"Тест с id {test_id} не найден")
            upd = update(TestOrm).where(TestOrm.id == test_id).values(link=new_link)
            await self.db.session.execute(upd)
        await self.db.session.commit()

    async def create_test(self, data: TestCreate) -> TestResponse:
        test = TestAdd(id=uuid.uuid4(), **data.model_dump())
        created = await self.db.tests.add(test)
        await self.db.commit()
        return TestResponse.model_validate(created)

    async def update_test(self, test_id: uuid.UUID, data: TestUpdate) -> TestResponse:
        existing = await self.db.tests.get_one_or_none(id=test_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.tests.edit(data, exclude_unset=True, id=test_id)
        await self.db.commit()
        updated = await self.db.tests.get_one(id=test_id)
        return TestResponse.model_validate(updated)

    async def delete_test(self, test_id: uuid.UUID) -> None:
        existing = await self.db.tests.get_one_or_none(id=test_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.tests.delete(id=test_id)

    async def create_scale(
        self, test_id: uuid.UUID, data: ScaleCreate
    ) -> ScaleResponse:
        if not await self.db.tests.get_one_or_none(id=test_id):
            raise ObjectNotFoundException()
        scale = ScaleAdd(
            id=uuid.uuid4(),
            title=data.title,
            min=data.min,
            max=data.max,
            test_id=test_id,
        )
        created = await self.db.scales.add(scale)
        await self.db.commit()
        return ScaleResponse.model_validate(created)

    async def update_scale(
        self, scale_id: uuid.UUID, data: ScaleUpdate
    ) -> ScaleResponse:
        existing = await self.db.scales.get_one_or_none(id=scale_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.scales.edit(data, exclude_unset=True, id=scale_id)
        await self.db.commit()
        updated = await self.db.scales.get_one(id=scale_id)
        return ScaleResponse.model_validate(updated)

    async def delete_scale(self, scale_id: uuid.UUID) -> None:
        existing = await self.db.scales.get_one_or_none(id=scale_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.scales.delete(id=scale_id)

    async def create_border(
        self, scale_id: uuid.UUID, data: BorderCreate
    ) -> BorderResponse:
        if not await self.db.scales.get_one_or_none(id=scale_id):
            raise ObjectNotFoundException()
        border = BordersAdd(
            id=uuid.uuid4(),
            left_border=data.left_border,
            right_border=data.right_border,
            color=data.color,
            title=data.title,
            user_recommendation=data.user_recommendation,
            scale_id=scale_id,
        )
        created = await self.db.borders.add(border)
        await self.db.commit()
        return BorderResponse.model_validate(created)

    async def update_border(
        self, border_id: uuid.UUID, data: BordersUpdate
    ) -> BorderResponse:
        existing = await self.db.borders.get_one_or_none(id=border_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.borders.edit(data, exclude_unset=True, id=border_id)
        await self.db.commit()
        updated = await self.db.borders.get_one(id=border_id)
        return BorderResponse.model_validate(updated)

    async def delete_border(self, border_id: uuid.UUID) -> None:
        existing = await self.db.borders.get_one_or_none(id=border_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.borders.delete(id=border_id)

    async def create_question(
        self, test_id: uuid.UUID, data: QuestionCreate
    ) -> QuestionResponse:
        if not await self.db.tests.get_one_or_none(id=test_id):
            raise ObjectNotFoundException()
        question = Question(id=uuid.uuid4(), test_id=test_id, **data.model_dump())
        created = await self.db.question.add(question)
        await self.db.commit()
        return QuestionResponse.model_validate(created)

    async def update_question(
        self, question_id: uuid.UUID, data: QuestionUpdate
    ) -> QuestionResponse:
        existing = await self.db.question.get_one_or_none(id=question_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.question.edit(data, exclude_unset=True, id=question_id)
        await self.db.commit()
        updated = await self.db.question.get_one(id=question_id)
        return QuestionResponse.model_validate(updated)

    async def delete_question(self, question_id: uuid.UUID) -> None:
        existing = await self.db.question.get_one_or_none(id=question_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.question.delete(id=question_id)

    async def create_answer_choice(
        self, data: AnswerChoiceCreate
    ) -> AnswerChoiceResponse:
        answer = AnswerChoice(id=uuid.uuid4(), **data.model_dump())
        created = await self.db.answer_choice.add(answer)
        await self.db.commit()
        return AnswerChoiceResponse.model_validate(created)

    async def update_answer_choice(
        self, answer_id: uuid.UUID, data: AnswerChoiceUpdate
    ) -> AnswerChoiceResponse:
        existing = await self.db.answer_choice.get_one_or_none(id=answer_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.answer_choice.edit(data, exclude_unset=True, id=answer_id)
        await self.db.commit()
        updated = await self.db.answer_choice.get_one(id=answer_id)
        return AnswerChoiceResponse.model_validate(updated)

    async def delete_answer_choice(self, answer_id: uuid.UUID) -> None:
        existing = await self.db.answer_choice.get_one_or_none(id=answer_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.answer_choice.delete(id=answer_id)

    def load_borders_for_scale(self, scale_id: uuid.UUID) -> list[dict]:
        with open(
            data_path("src/services/info/borders_info.json"), encoding="utf-8"
        ) as file:
            borders_data = json.load(file)
        filtered_borders = [
            border for border in borders_data if border["scale_id"] == str(scale_id)
        ]
        return filtered_borders

    async def add_tests(self, tests_data):
        tests = [TestAdd.model_validate(test) for test in tests_data]
        created, skipped = (0, 0)
        for test in tests:
            try:
                existing_test = await self.db.tests.get_one_or_none(id=test.id)
                if existing_test:
                    skipped += 1
                else:
                    await self.db.tests.add(test)
                    created += 1
            except ObjectAlreadyExistsException:
                skipped += 1
            except Exception as ex:
                logger.error(f"Ошибка при добавлении теста: {ex}")
                await self.db.rollback()
                raise MyAppException()
        if created > 0:
            logger.info(f"{created} тест(ов) успешно добавлено.")
        elif skipped > 0:
            logger.info("Все тесты уже существуют в базе.")
        else:
            logger.info("Файл тестов пустой, ничего не добавлено.")

    async def add_scales_and_borders(self, scales_data):
        scales = [ScaleAdd.model_validate(scale) for scale in scales_data]
        created_scales, skipped_scales = (0, 0)
        created_borders, updated_borders, skipped_borders = (0, 0, 0)
        for scale in scales:
            try:
                if not scale.test_id:
                    continue
                test = await self.db.tests.get_one_or_none(id=scale.test_id)
                if not test:
                    continue
                existing_scale = await self.db.scales.get_one_or_none(id=scale.id)
                if existing_scale:
                    skipped_scales += 1
                else:
                    await self.db.scales.add(scale)
                    created_scales += 1
                borders_data = self.load_borders_for_scale(scale.id)
                borders = [BordersAdd.model_validate(border) for border in borders_data]
                for border in borders:
                    try:
                        await self.db.borders.delete(id=border.id)
                        updated_borders += 1
                        await self.db.borders.add(border)
                        created_borders += 1
                    except ObjectNotFoundException:
                        await self.db.borders.add(border)
                        created_borders += 1
                    except Exception as ex:
                        await self.db.rollback()
                        raise MyAppException()
            except Exception as ex:
                await self.db.rollback()
                raise MyAppException()
        logger.info(
            f"Шкалы: {created_scales} добавлено, {skipped_scales} уже существовали. \nГраницы: {created_borders} добавлено, {updated_borders} обновлено, {skipped_borders} пропущено."
        )

    async def add_answer_choices(self, answer_choices_data):
        answer_choices = [
            AnswerChoice.model_validate(answer) for answer in answer_choices_data
        ]
        created, skipped = (0, 0)
        for answer in answer_choices:
            try:
                existing_answer = await self.db.answer_choice.get_one_or_none(
                    id=answer.id
                )
                if existing_answer:
                    skipped += 1
                else:
                    await self.db.answer_choice.add(answer)
                    created += 1
            except ObjectAlreadyExistsException:
                skipped += 1
            except Exception as ex:
                await self.db.rollback()
                raise MyAppException()
        if created > 0:
            logger.info(f"{created} ответ(ов) успешно добавлено.")
        elif skipped > 0:
            logger.info("Все ответы уже существуют в базе.")
        else:
            logger.info("Файл ответов пустой, ничего не добавлено.")

    async def add_questions(self, questions_data):
        questions = [Question.model_validate(question) for question in questions_data]
        created, skipped = (0, 0)
        for question in questions:
            try:
                existing_question = await self.db.question.get_one_or_none(
                    id=question.id
                )
                if existing_question:
                    skipped += 1
                else:
                    logger.debug(question)
                    await self.db.question.add(question)
                    created += 1
            except ObjectAlreadyExistsException:
                skipped += 1
            except Exception as ex:
                await self.db.rollback()
                raise MyAppException()
        if created > 0:
            logger.info(f"{created} вопрос(ов) успешно добавлено.")
        elif skipped > 0:
            logger.info("Все вопросы уже существуют в базе.")
        else:
            logger.info("Файл вопросов пустой, ничего не добавлено.")

    async def auto_create(self):
        from src.services.catalog import seed_catalog

        return await seed_catalog(self.db)

    async def all_tests(self) -> list[Dict[str, Any]]:
        try:
            tests = await self.db.tests.get_all()
            result = []
            for test in tests:
                test_data = {
                    "id": test.id,
                    "title": test.title,
                    "description": test.description,
                    "short_desc": test.short_desc,
                    "link": test.link,
                }
                result.append(test_data)
            return result
        except Exception as ex:
            logger.error(f"Ошибка при получении списка тестов: {ex}")
            await self.db.rollback()
            raise MyAppException()

    async def test_by_id(self, test_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        try:
            test = await self.db.tests.get_one(id=test_id)
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
            questions = await self.db.question.get_filtered(test_id=test_id)
            if not questions:
                raise ObjectNotFoundException()
            result = []
            for question in questions:
                question_data = {
                    "id": question.id,
                    "text": question.text,
                    "opposite_text": question.opposite_text,
                    "number": question.number,
                    "test_id": question.test_id,
                    "answer_choice": question.answer_choice,
                }
                result.append(question_data)
            return result
        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении вопросов: {ex}")
            raise MyAppException()

    async def test_questions_with_answers(
        self, test_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        try:
            questions = await self.db.question.get_filtered(test_id=test_id)
            if not questions:
                raise ObjectNotFoundException()
            all_answer_ids = []
            for question in questions:
                all_answer_ids.extend(question.answer_choice)
            answers = await self.db.answer_choice.get_by_ids(all_answer_ids)
            answer_dict = {answer.id: answer for answer in answers}
            result = []
            for question in questions:
                question_answers = []
                for answer_id in question.answer_choice:
                    answer = answer_dict.get(answer_id)
                    if answer:
                        question_answers.append(
                            {
                                "id": answer.id,
                                "text": answer.text,
                                "score": answer.score,
                            }
                        )
                question_data = {
                    "id": question.id,
                    "text": question.text,
                    "opposite_text": question.opposite_text,
                    "number": question.number,
                    "test_id": question.test_id,
                    "answer_choices": question_answers,
                }
                result.append(question_data)
            return result
        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении вопросов: {ex}")
            raise MyAppException()

    async def answers_by_question_id(
        self, test_id: uuid.UUID, question_id: uuid.UUID
    ) -> list[AnswerChoiceOrm]:
        """
        Получает все ответы, связанные с вопросом по его ID, и проверяет, что вопрос принадлежит указанному тесту.
        """
        try:
            test = await self.db.tests.get_one_or_none(id=test_id)
            if not test:
                raise ObjectNotFoundException()
            question = await self.db.question.get_one_or_none(
                id=question_id, test_id=test_id
            )
            if not question:
                raise ObjectNotFoundException()
            answers = []
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
            test = await self.db.tests.get_one(test_id)
            if not test:
                raise ObjectNotFoundException()
            scales = await self.db.scales.get_filtered(test_id=test_id)
            scale_details = []
            for scale in scales:
                borders = await self.db.borders.get_filtered(scale_id=scale.id)
                scale_details.append(
                    ScaleDetail(
                        id=scale.id,
                        title=scale.title,
                        min=scale.min,
                        max=scale.max,
                        borders=[
                            BorderDetail(
                                id=border.id,
                                left_border=border.left_border,
                                right_border=border.right_border,
                                color=border.color,
                                title=border.title,
                                user_recommendation=border.user_recommendation,
                            )
                            for border in borders
                        ],
                    )
                )
            questions = await self.db.question.get_filtered(test_id=test_id)
            question_details = []
            for question in questions:
                answers = []
                for answer_id in question.answer_choice:
                    answers.extend(
                        await self.db.answer_choice.get_filtered(id=answer_id)
                    )
                question_details.append(
                    QuestionDetail(
                        id=question.id,
                        text=question.text,
                        opposite_text=question.opposite_text,
                        number=question.number,
                        answers=[
                            AnswerChoiceDetail(
                                id=answer.id, text=answer.text, score=answer.score
                            )
                            for answer in answers
                        ],
                    )
                )
            return TestDetailsResponse(
                id=test.id,
                title=test.title,
                description=test.description,
                short_desc=test.short_desc,
                link=test.link,
                scales=scale_details,
                questions=question_details,
            )
        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении теста: {ex}")
            raise MyAppException()

    async def save_result(
        self, test_result_data: TestResultRequest, user_id: uuid.UUID
    ):
        try:
            test = await self.db.tests.get_one(id=test_result_data.test_id)
            if not test:
                raise ObjectNotFoundException()
            questions = await self.db.question.get_filtered(
                test_id=test_result_data.test_id
            )
            if not questions:
                raise ObjectNotFoundException()
            questions.sort(key=lambda question: (question.number, str(question.id)))
            answers = await self.db.answer_choice.get_by_ids(
                list(
                    {
                        answer
                        for question in questions
                        for answer in question.answer_choice
                    }
                )
            )
            valid_scores = {str(answer.id): answer.score for answer in answers}
            if len(test_result_data.results) != len(questions):
                raise InvalidAnswersCountError()
            for question, submitted in zip(questions, test_result_data.results):
                permitted = {
                    valid_scores[str(answer)]
                    for answer in question.answer_choice
                    if str(answer) in valid_scores
                }
                if submitted not in permitted:
                    raise HTTPException(
                        400, "Ответ отсутствует среди вариантов вопроса"
                    )
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
                "Стрессоустойчивость — это про меня?": calculator_service.test_stress_calculate_results,
                "Ищем причины выгорания": calculator_service.test_bat_calculate_results,
                "Почему я ждал этого?": calculator_service.test_leasy_calculate_results,
                "Что мне свойственно?": calculator_service.test_five_factors_calculate_results,
                "Как я чувствую себя в данный момент?": calculator_service.test_san_calculate_results,
            }
            calculation_methods_by_id = {
                "c9386cd7-4f63-4cbb-af35-54829ef9c14b": calculator_service.test_maslach_calculate_results,
                "bc9f1204-ea5d-40b0-b367-359bf9b2cc21": calculator_service.test_dass21_calculate_results,
                "3a9a3c8d-348e-4f0d-aefd-0feaa960ac25": calculator_service.test_stai_calculate_results,
                "f45c4528-ce69-4683-822a-91ffc52d55ba": calculator_service.test_coling_calculate_results,
                "d7bdba0c-f5ec-410d-9b53-3bfbf20c674a": calculator_service.test_cmq_calculate_results,
                "33d10952-aed7-4a4e-9e5a-dbd01b2f294d": calculator_service.test_back_calculate_results,
                "6c242c64-b8c0-4f5c-877f-91b1c1d3f5af": calculator_service.test_jas_calculate_results,
                "f56b5284-323e-42db-bd74-c80e8a5dc29a": calculator_service.test_stress_calculate_results,
                "ea869ca2-4e8f-4a98-8b13-4fbeedf30539": calculator_service.test_bat_calculate_results,
                "c18d71a4-7a8b-4b32-9e2a-3f8e5d6c7b9a": calculator_service.test_leasy_calculate_results,
                "e89f7acb-cd31-4d27-aadd-24f6c7d52794": calculator_service.test_five_factors_calculate_results,
                "a1b2c3d4-e5f6-7890-abcd-ef1234567890": calculator_service.test_san_calculate_results,
                "d8b4371d-9a11-5b6a-8c5f-7ce3509ed8d4": calculator_service.test_tipi_ru_calculate_results,
            }
            calculate_method = calculation_methods_by_id.get(
                str(test.id)
            ) or calculation_methods.get(test.title)
            if not calculate_method:
                raise ObjectNotFoundException()
            scale_sum_list = calculate_method(test_result_data.results)
            logger.debug("Расчёт теста завершён")
            if len(scale_sum_list) != len(scales):
                raise ResultsScaleMismatchError()
            try:
                test_res_id = uuid.uuid4()
                test_res = TestSaveResult(
                    id=test_res_id,
                    user_id=user_id,
                    test_id=test.id,
                    date=datetime.datetime.now(),
                )
                await self.db.test_result.add(test_res)
                await self.db.session.flush()
                try:
                    scales_info = load_data("src/services/info/scale_info.json")
                except Exception:
                    scales_info = []
                scale_desc_map = {
                    s["id"]: s.get("description", "") for s in scales_info
                }
                result = []
                _unused_scale_results = []
                for scale, score in zip(scales, scale_sum_list):
                    if score < scale.min or score > scale.max:
                        raise ScoreOutOfBoundsError()
                    borders = await self.db.borders.get_filtered(scale_id=scale.id)
                    if not borders:
                        raise ObjectNotFoundException()
                    scale_result = ScaleResult(
                        id=uuid.uuid4(),
                        score=score,
                        scale_id=scale.id,
                        test_result_id=test_res_id,
                    )
                    await self.db.scale_result.add(scale_result)
                    for border in borders:
                        if border.left_border <= score <= border.right_border:
                            result.append(
                                {
                                    "scale_id": str(scale.id),
                                    "scale_title": scale.title,
                                    "score": score,
                                    "conclusion": border.title,
                                    "color": border.color,
                                    "user_recommendation": border.user_recommendation,
                                    "description": scale_desc_map.get(
                                        str(scale.id), ""
                                    ),
                                }
                            )
                            _unused_scale_results.append(
                                {"scale_title": scale.title, "score": score}
                            )
                            break
                    else:
                        raise ObjectNotFoundException()
                await self.db.session.commit()
                return {"test_result_id": str(test_res_id), "result": result}
            except HTTPException:
                await self.db.session.rollback()
                raise
            except (
                ObjectNotFoundException,
                InvalidAnswersCountError,
                ResultsScaleMismatchError,
                ScoreOutOfBoundsError,
            ):
                await self.db.session.rollback()
                raise
            except Exception as e:
                await self.db.session.rollback()
                logger.error(f"Ошибка сохранения: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка сохранения результатов",
                )
        except HTTPException:
            raise
        except (
            ObjectNotFoundException,
            InvalidAnswersCountError,
            ResultsScaleMismatchError,
            ScoreOutOfBoundsError,
        ):
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Произошла непредвиденная ошибка",
            )

    async def get_test_result_by_user_and_test(
        self, test_id: uuid.UUID, user_id: uuid.UUID, current_user_id: uuid.UUID
    ):
        try:
            relation = await self.db.clients.get_one_or_none(
                client_id=user_id, mentor_id=current_user_id, status=True
            )
            if not relation:
                raise ObjectNotFoundException(
                    f"Клиент с ID {user_id} не найден или не является вашим подопечным"
                )
            test_results = await self.db.test_result.get_filtered(
                test_id=test_id, user_id=user_id
            )
            results = []
            for test_result in test_results:
                scale_results = await self.db.scale_result.get_filtered(
                    test_result_id=test_result.id
                )
                result = {
                    "test_id": str(test_result.test_id),
                    "test_result_id": str(test_result.id),
                    "datetime": test_result.date.isoformat(),
                    "scale_results": [],
                }
                for sr in scale_results:
                    scale = await self.db.scales.get_one(id=sr.scale_id)
                    if not scale:
                        continue
                    borders = await self.db.borders.get_filtered(scale_id=scale.id)
                    conclusion = ""
                    color = ""
                    user_recommendation = ""
                    for border in borders:
                        if border.left_border <= sr.score <= border.right_border:
                            conclusion = border.title
                            color = border.color
                            user_recommendation = border.user_recommendation
                            break
                    result["scale_results"].append(
                        {
                            "scale_id": str(scale.id),
                            "scale_title": scale.title,
                            "score": sr.score,
                            "max_score": scale.max,
                            "conclusion": conclusion,
                            "color": color,
                            "user_recommendation": user_recommendation,
                        }
                    )
                results.append(result)
            return results
        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении результатов теста: {ex}")
            raise MyAppException()

    async def get_test_result_by_user_and_test_not_psyc(
        self, test_id: uuid.UUID, user_id: uuid.UUID
    ):
        try:
            test_results = await self.db.test_result.get_filtered(
                test_id=test_id, user_id=user_id
            )
            results = []
            try:
                scales_info = load_data("src/services/info/scale_info.json")
            except Exception:
                scales_info = []
            scale_desc_map = {s["id"]: s.get("description", "") for s in scales_info}
            for test_result in test_results:
                scale_results = await self.db.scale_result.get_filtered(
                    test_result_id=test_result.id
                )
                result = {
                    "test_id": str(test_result.test_id),
                    "test_result_id": str(test_result.id),
                    "datetime": test_result.date.isoformat(),
                    "scale_results": [],
                }
                for sr in scale_results:
                    scale = await self.db.scales.get_one(id=sr.scale_id)
                    if not scale:
                        continue
                    borders = await self.db.borders.get_filtered(scale_id=scale.id)
                    conclusion = ""
                    color = ""
                    user_recommendation = ""
                    for border in borders:
                        if border.left_border <= sr.score <= border.right_border:
                            conclusion = border.title
                            color = border.color
                            user_recommendation = border.user_recommendation
                            break
                    result["scale_results"].append(
                        {
                            "scale_id": str(scale.id),
                            "scale_title": scale.title,
                            "score": sr.score,
                            "max_score": scale.max,
                            "conclusion": conclusion,
                            "color": color,
                            "user_recommendation": user_recommendation,
                            "description": scale_desc_map.get(str(scale.id), ""),
                        }
                    )
                results.append(result)
            return results
        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении результатов теста: {ex}")
            raise MyAppException()

    async def get_test_result_by_id(
        self, result_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Получает результат теста по его ID с проверкой прав доступа.
        """
        try:
            current_user = await self.db.users.get_one(id=current_user_id)
            current_user_role = current_user.role_id
            test_result = await self.db.test_result.get_one(id=result_id)
            if not test_result:
                raise ObjectNotFoundException()
            if current_user_role == 0:
                pass
            elif current_user_role == 2:
                if test_result.user_id == current_user_id:
                    pass
                else:
                    relation = await self.db.clients.get_one_or_none(
                        client_id=test_result.user_id,
                        mentor_id=current_user_id,
                        status=True,
                    )
                    if not relation:
                        raise ObjectNotFoundException(
                            "Результат не найден или доступ запрещён"
                        )
            elif test_result.user_id != current_user_id:
                raise ObjectNotFoundException("Результат не найден или доступ запрещён")
            scale_results = await self.db.scale_result.get_filtered(
                test_result_id=test_result.id
            )
            result = {
                "test_id": str(test_result.test_id),
                "test_result_id": str(test_result.id),
                "datetime": test_result.date.isoformat(),
                "scale_results": [],
            }
            try:
                scales_info = load_data("src/services/info/scale_info.json")
            except Exception:
                scales_info = []
            scale_desc_map = {s["id"]: s.get("description", "") for s in scales_info}
            for sr in scale_results:
                scale = await self.db.scales.get_one(id=sr.scale_id)
                if not scale:
                    continue
                borders = await self.db.borders.get_filtered(scale_id=scale.id)
                conclusion = ""
                color = ""
                user_recommendation = ""
                for border in borders:
                    if border.left_border <= sr.score <= border.right_border:
                        conclusion = border.title
                        color = border.color
                        user_recommendation = border.user_recommendation
                        break
                result["scale_results"].append(
                    {
                        "scale_id": str(scale.id),
                        "scale_title": scale.title,
                        "score": sr.score,
                        "max_score": scale.max,
                        "conclusion": conclusion,
                        "color": color,
                        "user_recommendation": user_recommendation,
                        "description": scale_desc_map.get(str(scale.id), ""),
                    }
                )
            return result
        except ObjectNotFoundException:
            raise ObjectNotFoundException()
        except Exception as ex:
            logger.error(f"Ошибка при получении результата теста: {ex}")
            raise MyAppException()

    async def get_passed_tests_by_user(
        self, user_id: uuid.UUID
    ) -> list[Dict[str, Any]]:
        try:
            test_results = await self.db.test_result.get_filtered(user_id=user_id)
            if not test_results:
                return []
            test_ids = list(
                dict.fromkeys((uuid.UUID(str(tr.test_id)) for tr in test_results))
            )
            tests = await self.db.tests.get_by_ids(test_ids)
            if not tests:
                return []
            test_dict = {str(test.id): test for test in tests}
            passed_tests = []
            for test_id in test_ids:
                test = test_dict.get(str(test_id))
                if test:
                    passed_tests.append(
                        {
                            "title": test.title,
                            "description": test.description,
                            "test_id": str(test.id),
                            "link": test.link,
                        }
                    )
            return passed_tests
        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении пройденных тестов: {ex}")
            raise MyAppException()
