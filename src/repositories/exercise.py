from typing import List, Optional
import datetime
import uuid
from src.schemas.exercise import FieldType
from sqlalchemy import select, and_, update, exists
from sqlalchemy.orm import joinedload
from src.models.exercise import (
    ExerciseStructureOrm, FieldOrm, VariantOrm,
    CompletedExerciseOrm, FilledFieldOrm
)
from src.schemas.exercise import (
    ExerciseCreate, ExerciseResponse, ExerciseDetailResponse,
    FieldResponse, VariantResponse, FieldCreate, VariantCreate,
    CompletedExerciseCreate, PulledFieldResponse
)
from src.repositories.base import BaseRepository


class ExerciseRepository(BaseRepository):
    async def create_exercise(self, exercise_data: ExerciseCreate) -> ExerciseResponse:
        exercise = ExerciseStructureOrm(
            id=uuid.uuid4(),
            field_count=0,
            **exercise_data.model_dump()
        )
        self.session.add(exercise)
        await self.session.commit()
        await self.session.refresh(exercise)
        return ExerciseResponse.model_validate(exercise)

    async def create_field(self, exercise_id: uuid.UUID, field_data: FieldCreate) -> FieldResponse:
        exercise = await self.session.get(ExerciseStructureOrm, exercise_id)
        if not exercise:
            raise ValueError("Exercise not found")

        exercises = [
            str(ex_id) for ex_id in field_data.exercises] if field_data.exercises else None

        field = FieldOrm(
            id=uuid.uuid4(),
            exercise_structure_id=exercise_id,
            type=field_data.type,
            title=field_data.title,
            hint=field_data.hint,
            description=field_data.description,
            major=field_data.major,
            order=field_data.order,
            exercises=exercises,
            variants=[]
        )
        self.session.add(field)
        exercise.field_count += 1
        await self.session.commit()
        await self.session.refresh(field)

        return FieldResponse(
            id=field.id,
            title=field.title,
            hint=field.hint,
            description=field.description,
            type=field.type.value,
            major=field.major,
            order=field.order,
            exercises=field.exercises,
            exercise_structure_id=field.exercise_structure_id,
            variants=[]
        )

    async def exercise_exists(self, exercise_id: uuid.UUID) -> bool:
        result = await self.session.scalar(
            select(ExerciseStructureOrm)
            .where(ExerciseStructureOrm.id == exercise_id)
        )
        return result is not None

    async def get_field(self, field_id: uuid.UUID) -> Optional[FieldOrm]:
        result = await self.session.execute(
            select(FieldOrm)
            .where(FieldOrm.id == field_id)
            .options(joinedload(FieldOrm.variants))
        )
        return result.scalars().first()

    async def create_variant(self, field_id: uuid.UUID, variant_data: VariantCreate) -> VariantResponse:
        variant = VariantOrm(
            id=uuid.uuid4(),
            field_id=field_id,
            title=variant_data.title
        )
        self.session.add(variant)
        await self.session.commit()
        await self.session.refresh(variant)

        return VariantResponse(
            id=variant.id,
            title=variant.title,
            field_id=variant.field_id
        )

    async def get_all_exercises(self, user_id: Optional[uuid.UUID] = None) -> List[ExerciseResponse]:
        query = select(ExerciseStructureOrm)
        result = await self.session.execute(query)
        exercises = result.scalars().all()

        response = []
        for exercise in exercises:
            exercise_resp = ExerciseResponse.model_validate(exercise)

            if user_id:
                if exercise.linked_exercise_id is None:
                    exercise_resp.open = True
                else:
                    prev_completed = await self.session.scalar(
                        select(CompletedExerciseOrm)
                        .where(and_(
                            CompletedExerciseOrm.exercise_structure_id == exercise.linked_exercise_id,
                            CompletedExerciseOrm.user_id == user_id
                        ))
                    )
                    exercise_resp.open = prev_completed is not None

            response.append(exercise_resp)

        return response

    async def get_exercise_by_id(self, exercise_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> ExerciseDetailResponse:
        # Получаем упражнение с его полями и вариантами
        exercise = await self.session.execute(
            select(ExerciseStructureOrm)
            .where(ExerciseStructureOrm.id == exercise_id)
            .options(
                joinedload(ExerciseStructureOrm.field)
                .joinedload(FieldOrm.variants)
            )
        )
        exercise = exercise.scalars().unique().first()

        if not exercise:
            return None

        # Получаем все заполненные поля, которые должны быть стянуты в это упражнение
        pulled_fields_query = await self.session.execute(
            select(FilledFieldOrm, CompletedExerciseOrm)
            .join(FieldOrm, FieldOrm.id == FilledFieldOrm.field_id)
            .join(CompletedExerciseOrm, CompletedExerciseOrm.id == FilledFieldOrm.completed_exercise_id)
            .where(
                FieldOrm.exercises.any(str(exercise_id)),
                CompletedExerciseOrm.user_id == user_id if user_id else True
            )
        )
        
        pulled_fields = [
            PulledFieldResponse(
                field_id=field.field_id,
                text=field.text,
                source_exercise_id=completed_exercise.exercise_structure_id
            )
            for field, completed_exercise in pulled_fields_query
        ]

        # Создаем ответ с упражнением, стянутыми полями и полями упражнения
        exercise_resp = ExerciseDetailResponse(
            id=exercise.id,
            title=exercise.title,
            description=exercise.description,
            picture_link=exercise.picture_link,
            linked_exercise_id=exercise.linked_exercise_id,
            field_count=exercise.field_count,
            pulled_fields=pulled_fields,
            fields=[
                FieldResponse(
                    id=field.id,
                    title=field.title,
                    hint=field.hint,
                    description=field.description,
                    type=field.type,
                    major=field.major,
                    order=field.order,
                    exercises=field.exercises,
                    exercise_structure_id=field.exercise_structure_id,
                    variants=[
                        VariantResponse(
                            id=variant.id,
                            title=variant.title,
                            field_id=variant.field_id
                        ) for variant in field.variants
                    ]
                ) for field in exercise.field
            ]
        )

        if user_id:
            if exercise.linked_exercise_id is None:
                exercise_resp.open = True
            else:
                prev_completed = await self.session.scalar(
                    select(CompletedExerciseOrm)
                    .where(and_(
                        CompletedExerciseOrm.exercise_structure_id == exercise.linked_exercise_id,
                        CompletedExerciseOrm.user_id == user_id
                    ))
                )
                exercise_resp.open = prev_completed is not None

        return exercise_resp

    async def complete_exercise(self, user_id: uuid.UUID, completed_data: CompletedExerciseCreate) -> None:
        # Получаем упражнение с явной загрузкой полей
        exercise = await self.session.execute(
            select(ExerciseStructureOrm)
            .where(ExerciseStructureOrm.id == completed_data.exercise_structure_id)
            .options(joinedload(ExerciseStructureOrm.field))
        )
        exercise = exercise.scalars().unique().first()

        if not exercise:
            raise ValueError("Exercise not found")

        # Получаем ID обязательных полей
        required_field_ids = {field.id for field in exercise.field if field.major}
        provided_field_ids = {field.field_id for field in completed_data.filled_fields}

        if not required_field_ids.issubset(provided_field_ids):
            missing_fields = required_field_ids - provided_field_ids
            raise ValueError(f"Missing answers for required fields: {missing_fields}")

        # Создаем запись о выполненном упражнении
        completed = CompletedExerciseOrm(
            id=uuid.uuid4(),
            user_id=user_id,
            exercise_structure_id=completed_data.exercise_structure_id,
            date=datetime.datetime.now()
        )
        self.session.add(completed)
        await self.session.flush()  # Нужно для получения ID

        # Создаем заполненные поля
        for field_data in completed_data.filled_fields:
            # Проверяем существование поля
            field_exists = await self.session.scalar(
                select(exists().where(FieldOrm.id == field_data.field_id)))
            if not field_exists:
                raise ValueError(f"Field with id {field_data.field_id} not found")

            filled_field = FilledFieldOrm(
                id=uuid.uuid4(),
                completed_exercise_id=completed.id,
                field_id=field_data.field_id,
                text=field_data.text,
                exercises=field_data.exercises or None
            )
            self.session.add(filled_field)

        await self.session.commit()
