import json
import uuid
from src.schemas.tests import TestAdd, ScaleAdd, BordersAdd, AnswerChoice, Question
from src.services.base import BaseService

class TestService(BaseService):

    async def auto_create(self):
        with open("services/info/test_info.json", encoding="utf-8") as file:
            tests_data = json.load(file)

        tests = [TestAdd.model_validate(test) for test in tests_data]

        for test in tests:
            try:
                existing_test = await self.db.tests.get_one_or_none(id=test.id)
                if existing_test:
                    print(f"Тест с id={test.id} уже существует. Пропускаем.")
                else:
                    await self.db.tests.add(test)
                    print(f"Тест с id={test.id} добавлен.")
            except Exception as ex:
                print(f"Ошибка при добавлении теста: {ex}")
                await self.db.rollback()

        with open("services/info/scale_info.json", encoding="utf-8") as file:
            scales_data = json.load(file)

        scales = [ScaleAdd.model_validate(scale) for scale in scales_data]

        for scale in scales:
            try:

                test = await self.db.tests.get_one_or_none(title=scale.title)
                if not test:
                    print(f"Тест для шкалы '{scale.title}' не найден. Пропускаем.")
                    continue

                scale.test_id = test.id

                existing_scale = await self.db.scales.get_one_or_none(id=scale.id)
                if existing_scale:
                    print(f"Шкала с id={scale.id} уже существует. Пропускаем.")
                else:
                    await self.db.scales.add(scale)
                    print(f"Шкала с id={scale.id} добавлена и связана с тестом {test.id}.")

                    borders_data = self._load_borders_for_scale(scale.id)
                    borders = [BordersAdd.model_validate(border) for border in borders_data]

                    for border in borders:
                        try:
                            await self.db.borders.add(border)
                            print(f"Граница для шкалы {scale.id} добавлена.")
                        except Exception as ex:
                            print(f"Ошибка при добавлении границы: {ex}")
                            await self.db.rollback()

            except Exception as ex:
                print(f"Ошибка при добавлении шкалы: {ex}")
                await self.db.rollback()

        with open("services/info/answer_choices_info.json", encoding="utf-8") as file:
            answer_choices_data = json.load(file)

        answer_choices = [AnswerChoice.model_validate(answer) for answer in answer_choices_data]

        for answer in answer_choices:
            try:
                existing_answer = await self.db.answer_choice.get_one_or_none(id=answer.id)
                if existing_answer:
                    print(f"Ответ с id={answer.id} уже существует. Пропускаем.")
                else:
                    await self.db.answer_choice.add(answer)
                    print(f"Ответ с id={answer.id} добавлен.")
            except Exception as ex:
                print(f"Ошибка при добавлении ответа: {ex}")
                await self.db.rollback()

        with open("services/info/questions_info.json", encoding="utf-8") as file:
            questions_data = json.load(file)

        questions = [Question.model_validate(question) for question in questions_data]

        for question in questions:
            try:
                existing_question = await self.db.question.get_one_or_none(id=question.id)
                if existing_question:
                    print(f"Вопрос с id={question.id} уже существует. Пропускаем.")
                else:
                    await self.db.question.add(question)
                    print(f"Вопрос с id={question.id} добавлен.")
            except Exception as ex:
                print(f"Ошибка при добавлении вопроса: {ex}")
                await self.db.rollback()

        await self.db.commit()
        return {"status": "OK", "message": "Тесты, шкалы, границы, ответы и вопросы успешно созданы или пропущены"}

    def _load_borders_for_scale(self, scale_id: uuid.UUID) -> list[dict]:
        with open("services/info/borders_info.json", encoding="utf-8") as file:
            borders_data = json.load(file)

        filtered_borders = [border for border in borders_data if border["scale_id"] == str(scale_id)]

        return filtered_borders