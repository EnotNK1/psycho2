import uuid
from typing import List

from src.services.base import BaseService
from src.services.fixtures.training_exercise import TRAINING_EXERCISES
from src.exceptions import ObjectNotFoundException
from src.schemas.training_exercise import (
    ExerciseShortResponse,
    ExerciseDetailResponse,
)
from src.models.training_exercises import (
    TrainingExerciseOrm,
    TrainingQuestionOrm,
    TrainingVariantOrm,
    TrainingCompletedExerciseOrm
)


class TrainingExerciseService(BaseService):

    async def seed_exercises(self):
        for ex_data in TRAINING_EXERCISES:

            ex_id = uuid.UUID(ex_data["id"])

            existing = await self.db.training_exercise.get_by_id(ex_id)

            if existing:
                # обновляем базовые поля
                existing.title = ex_data["title"]
                existing.description = ex_data["description"]
                existing.picture_link = ex_data["picture_link"]
                existing.time_to_read = ex_data["time_to_read"]

                # удаляем старые вопросы (cascade удалит варианты)
                await self.db.training_exercise.delete_questions(ex_id)

                exercise = existing
            else:
                exercise = TrainingExerciseOrm(
                    id=ex_id,
                    title=ex_data["title"],
                    description=ex_data["description"],
                    picture_link=ex_data["picture_link"],
                    time_to_read=ex_data["time_to_read"],
                )
                await self.db.training_exercise.add(exercise)

            await self.db.training_exercise.flush()

            # создаём вопросы
            for q in ex_data["questions"]:
                question = TrainingQuestionOrm(
                    text=q["text"],
                    formulation=q["formulation"],
                    training_exercise_id=exercise.id,
                )
                await self.db.training_exercise.add(question)
                await self.db.training_exercise.flush()

                # варианты
                for v in q["variants"]:
                    variant = TrainingVariantOrm(
                        title=v["title"],
                        correct=v["correct"],
                        explanation=v["explanation"],
                        question_id=question.id,
                    )
                    await self.db.training_exercise.add(variant)

        await self.db.commit()

    async def get_all_exercises(self, user_id) -> List[ExerciseShortResponse]:
        exercises = await self.db.training_exercise.get_all()

        result = []
        completed_ids = set()

        if user_id:
            completed_ids = await self.db.training_exercise.get_completed_map(user_id)

        for ex in exercises:
            result.append(
                ExerciseShortResponse(
                    id=ex.id,
                    title=ex.title,
                    picture_link=ex.picture_link,
                    is_completed=ex.id in completed_ids,
                )
            )
        return result

    async def get_exercise_by_id(self, exercise_id: uuid.UUID, user_id):
        exercise = await self.db.training_exercise.get_by_id(exercise_id)

        if not exercise:
            raise ObjectNotFoundException()

        is_completed = False
        if user_id:
            is_completed = await self.db.training_exercise.is_completed(exercise_id, user_id)

        return ExerciseDetailResponse(
            id=exercise.id,
            title=exercise.title,
            picture_link=exercise.picture_link,
            description=exercise.description,
            time_to_read=exercise.time_to_read,
            is_completed=is_completed,
        )

    async def get_exercise_structure_by_id(self, exercise_id: uuid.UUID, user_id):
        exercise = await self.db.training_exercise.get_with_structure(exercise_id)

        if not exercise:
            raise ObjectNotFoundException()
        return exercise

    async def is_exercise_completed_by_id(self, exercise_id: uuid.UUID, user_id):
        if not user_id:
            return {"is_completed": False}

        is_completed = await self.db.training_exercise.is_completed(exercise_id, user_id)

        return {"is_completed": is_completed}

    async def complete_exercise(self, exercise_id: uuid.UUID, user_id: uuid.UUID):
        existing = await self.db.training_completed_exercise.get_one_or_none(
            training_exercise_id=exercise_id,
            user_id=user_id
        )

        if existing:
            return

        completed = TrainingCompletedExerciseOrm(
            training_exercise_id=exercise_id,
            user_id=user_id,
        )

        await self.db.training_exercise.add(completed)
        await self.db.commit()
