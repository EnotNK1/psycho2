import uuid
from sqlalchemy import select, exists, and_, delete
from sqlalchemy.orm import selectinload

from src.models.training_exercises import (
    TrainingExerciseOrm,
    TrainingCompletedExerciseOrm,
    TrainingQuestionOrm,
    TrainingVariantOrm
)
from src.repositories.base import BaseRepository


class TrainingExerciseRepository(BaseRepository):
    model = TrainingExerciseOrm

    async def add(self, instance):
        self.session.add(instance)

    async def get_all(self):
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def get_by_id(self, exercise_id: uuid.UUID):
        result = await self.session.execute(
            select(self.model).filter_by(id=exercise_id)
        )
        return result.scalars().first()

    async def get_with_structure(self, exercise_id: uuid.UUID):
        result = await self.session.execute(
            select(self.model)
            .options(
                selectinload(self.model.questions)
                .selectinload(TrainingQuestionOrm.variants)
            )
            .filter_by(id=exercise_id)
        )
        return result.scalars().first()

    async def is_completed(self, exercise_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        query = select(
            exists().where(
                and_(
                    TrainingCompletedExerciseOrm.training_exercise_id == exercise_id,
                    TrainingCompletedExerciseOrm.user_id == user_id,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar()

    async def get_completed_map(self, user_id: uuid.UUID):
        result = await self.session.execute(
            select(TrainingCompletedExerciseOrm.training_exercise_id)
            .filter(TrainingCompletedExerciseOrm.user_id == user_id)
        )
        completed_ids = set(result.scalars().all())
        return completed_ids

    async def delete_questions(self, exercise_id):
        await self.session.execute(
            delete(TrainingQuestionOrm).where(
                TrainingQuestionOrm.training_exercise_id == exercise_id
            )
        )

    async def add_exercise(self, data):
        exercise = TrainingExerciseOrm(**data)
        self.session.add(exercise)
        return exercise

    async def flush(self):
        await self.session.flush()
