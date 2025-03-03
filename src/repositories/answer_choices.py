import uuid

from src.models.tests import AnswerChoiceOrm, QuestionOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import AnswerChoiceDataMapper
from src.repositories.tests import logger


class AnswerChoiceRepository(BaseRepository):
    model = AnswerChoiceOrm
    mapper = AnswerChoiceDataMapper

    async def all_by_question_id(self, question_id: uuid.UUID) -> list[AnswerChoiceOrm]:
        """
        Возвращает все ответы, связанные с вопросом по его ID.
        """
        try:
            question = await self.session.get(QuestionOrm, question_id)
            if not question:
                logger.warning(f"Вопрос с id={question_id} не найден.")
                return []

            # Replacing the old code with get_by_ids method
            return await self.get_by_ids(question.answer_choice)

        except Exception as ex:
            logger.error(f"Ошибка при получении ответов для вопроса {question_id}: {ex}")
            raise
