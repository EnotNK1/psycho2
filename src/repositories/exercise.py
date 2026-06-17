from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import and_, delete, exists, func, select
from sqlalchemy.orm import joinedload, selectinload

from src.models.exercise import (
    CompletedExerciseOrm,
    ExerciseStructureOrm,
    ExerciseViewOrm,
    FieldOrm,
    FilledFieldOrm,
    VariantOrm,
)
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import ExerciseMapper


class ExerciseRepository(BaseRepository):
    model = ExerciseStructureOrm
    mapper = ExerciseMapper

    async def create_exercise(self, exercise: ExerciseStructureOrm) -> ExerciseStructureOrm:
        self.session.add(exercise)
        await self.session.flush()
        await self.session.refresh(exercise)
        return exercise

    async def create_field(self, field: FieldOrm) -> FieldOrm:
        self.session.add(field)
        await self.session.flush()
        await self.session.refresh(field)
        return field

    async def create_variant(self, variant: VariantOrm) -> VariantOrm:
        self.session.add(variant)
        await self.session.flush()
        await self.session.refresh(variant)
        return variant

    async def create_exercise_view(self, view: ExerciseViewOrm) -> ExerciseViewOrm:
        self.session.add(view)
        await self.session.flush()
        await self.session.refresh(view)
        return view

    async def add(self, instance):
        self.session.add(instance)

    async def flush(self):
        await self.session.flush()

    async def update_exercise(self, exercise: ExerciseStructureOrm) -> ExerciseStructureOrm:
        await self.session.flush()
        await self.session.refresh(exercise)
        return exercise

    async def update_field(self, field: FieldOrm) -> FieldOrm:
        await self.session.flush()
        await self.session.refresh(field)
        return field

    async def update_variant(self, variant: VariantOrm) -> VariantOrm:
        await self.session.flush()
        await self.session.refresh(variant)
        return variant

    async def update_exercise_view(self, view: ExerciseViewOrm) -> ExerciseViewOrm:
        await self.session.flush()
        await self.session.refresh(view)
        return view

    async def delete_exercise(self, exercise: ExerciseStructureOrm) -> None:
        await self.session.delete(exercise)

    async def delete_field(self, field: FieldOrm) -> None:
        await self.session.delete(field)

    async def delete_variant(self, variant: VariantOrm) -> None:
        await self.session.delete(variant)

    async def delete_exercise_view(self, view: ExerciseViewOrm) -> None:
        await self.session.delete(view)

    async def delete_fields_by_exercise(self, exercise_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(FieldOrm).where(
                FieldOrm.exercise_structure_id == exercise_id)
        )

    async def delete_views_by_exercise(self, exercise_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(ExerciseViewOrm).where(
                ExerciseViewOrm.exercise_structure_id == exercise_id)
        )

    async def delete_stale_fields_without_results(
        self, exercise_id: uuid.UUID, actual_field_ids: set[uuid.UUID]
    ) -> None:
        conditions = [FieldOrm.exercise_structure_id == exercise_id]
        if actual_field_ids:
            conditions.append(FieldOrm.id.not_in(actual_field_ids))

        await self.session.execute(
            delete(FieldOrm).where(
                *conditions,
                ~exists().where(FilledFieldOrm.field_id == FieldOrm.id),
            )
        )

    async def delete_stale_variants(
        self, field_id: uuid.UUID, actual_variant_ids: set[uuid.UUID]
    ) -> None:
        conditions = [VariantOrm.field_id == field_id]
        if actual_variant_ids:
            conditions.append(VariantOrm.id.not_in(actual_variant_ids))

        await self.session.execute(delete(VariantOrm).where(*conditions))

    async def delete_stale_views(
        self, exercise_id: uuid.UUID, actual_view_ids: set[uuid.UUID]
    ) -> None:
        conditions = [ExerciseViewOrm.exercise_structure_id == exercise_id]
        if actual_view_ids:
            conditions.append(ExerciseViewOrm.id.not_in(actual_view_ids))

        await self.session.execute(delete(ExerciseViewOrm).where(*conditions))

    async def exercise_exists(self, exercise_id: uuid.UUID) -> bool:
        return await self.get_exercise_entity(exercise_id) is not None

    async def get_exercise_entity(self, exercise_id: uuid.UUID) -> Optional[ExerciseStructureOrm]:
        result = await self.session.execute(
            select(ExerciseStructureOrm).where(
                ExerciseStructureOrm.id == exercise_id)
        )
        return result.scalars().first()

    async def get_exercise_with_fields(self, exercise_id: uuid.UUID) -> Optional[ExerciseStructureOrm]:
        result = await self.session.execute(
            select(ExerciseStructureOrm)
            .where(ExerciseStructureOrm.id == exercise_id)
            .options(
                selectinload(ExerciseStructureOrm.field).selectinload(
                    FieldOrm.variants)
            )
        )
        return result.scalars().first()

    async def get_all_exercise_entities(self) -> list[ExerciseStructureOrm]:
        result = await self.session.execute(
            select(ExerciseStructureOrm).order_by(
                ExerciseStructureOrm.sort_order, ExerciseStructureOrm.id
            )
        )
        return result.scalars().all()

    async def get_completed_exercise_ids(
        self, user_id: uuid.UUID, exercise_ids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        if not exercise_ids:
            return set()

        result = await self.session.execute(
            select(CompletedExerciseOrm.exercise_structure_id)
            .where(
                CompletedExerciseOrm.user_id == user_id,
                CompletedExerciseOrm.exercise_structure_id.in_(exercise_ids),
            )
        )
        return set(result.scalars().all())

    async def is_exercise_completed(self, exercise_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        query = select(
            exists().where(
                and_(
                    CompletedExerciseOrm.exercise_structure_id == exercise_id,
                    CompletedExerciseOrm.user_id == user_id,
                )
            )
        )
        result = await self.session.execute(query)
        return bool(result.scalar())

    async def get_field(self, field_id: uuid.UUID) -> Optional[FieldOrm]:
        result = await self.session.execute(
            select(FieldOrm)
            .where(FieldOrm.id == field_id)
            .options(joinedload(FieldOrm.variants))
        )
        return result.scalars().first()

    async def get_fields_by_exercise(self, exercise_id: uuid.UUID) -> list[FieldOrm]:
        result = await self.session.execute(
            select(FieldOrm)
            .where(FieldOrm.exercise_structure_id == exercise_id)
            .options(selectinload(FieldOrm.variants))
        )
        return result.scalars().all()

    async def get_variant(self, variant_id: uuid.UUID) -> Optional[VariantOrm]:
        result = await self.session.execute(
            select(VariantOrm).where(VariantOrm.id == variant_id)
        )
        return result.scalars().first()

    async def get_variants_by_field(self, field_id: uuid.UUID) -> list[VariantOrm]:
        result = await self.session.execute(
            select(VariantOrm).where(VariantOrm.field_id == field_id)
        )
        return result.scalars().all()

    async def get_exercise_view(self, view_id: uuid.UUID) -> Optional[ExerciseViewOrm]:
        result = await self.session.execute(
            select(ExerciseViewOrm).where(ExerciseViewOrm.id == view_id)
        )
        return result.scalars().first()

    async def get_views_by_exercise(self, exercise_id: uuid.UUID) -> list[ExerciseViewOrm]:
        result = await self.session.execute(
            select(ExerciseViewOrm).where(
                ExerciseViewOrm.exercise_structure_id == exercise_id
            )
        )
        return result.scalars().all()

    async def get_latest_exercise_view(self, exercise_id: uuid.UUID) -> Optional[ExerciseViewOrm]:
        result = await self.session.execute(
            select(ExerciseViewOrm)
            .where(ExerciseViewOrm.exercise_structure_id == exercise_id)
            .order_by(ExerciseViewOrm.score.desc().nullslast(), ExerciseViewOrm.id.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def get_passed_exercises_by_user(self, user_id: uuid.UUID):
        latest_completed_subquery = (
            select(
                CompletedExerciseOrm.exercise_structure_id.label(
                    "exercise_id"),
                func.max(CompletedExerciseOrm.date).label("last_completed_at"),
            )
            .where(CompletedExerciseOrm.user_id == user_id)
            .group_by(CompletedExerciseOrm.exercise_structure_id)
            .subquery()
        )

        result = await self.session.execute(
            select(
                ExerciseStructureOrm.id,
                ExerciseStructureOrm.title,
                ExerciseStructureOrm.picture_link,
                latest_completed_subquery.c.last_completed_at,
            )
            .join(
                latest_completed_subquery,
                latest_completed_subquery.c.exercise_id == ExerciseStructureOrm.id,
            )
            .order_by(ExerciseStructureOrm.title)
        )
        return result.all()

    async def get_pulled_fields(
        self, exercise_id: uuid.UUID, user_id: Optional[uuid.UUID]
    ) -> list[tuple[FilledFieldOrm, CompletedExerciseOrm]]:
        if user_id is None:
            return []

        result = await self.session.execute(
            select(FilledFieldOrm, CompletedExerciseOrm)
            .join(
                CompletedExerciseOrm,
                CompletedExerciseOrm.id == FilledFieldOrm.completed_exercise_id,
            )
            .where(
                FilledFieldOrm.exercises.any(str(exercise_id)),
                CompletedExerciseOrm.user_id == user_id,
            )
            .order_by(
                CompletedExerciseOrm.date.desc(),
                FilledFieldOrm.source_group_key,
                FilledFieldOrm.id,
            )
        )
        return result.all()

    async def get_exercise_results(self, exercise_id: uuid.UUID, user_id: uuid.UUID):
        result = await self.session.execute(
            select(CompletedExerciseOrm)
            .where(
                CompletedExerciseOrm.exercise_structure_id == exercise_id,
                CompletedExerciseOrm.user_id == user_id,
            )
            .options(selectinload(CompletedExerciseOrm.filled_field))
            .order_by(CompletedExerciseOrm.date.desc())
        )
        return result.scalars().all()

    async def get_exercise_result_detail(
        self, exercise_id: uuid.UUID, result_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[CompletedExerciseOrm]:
        result = await self.session.execute(
            select(CompletedExerciseOrm)
            .where(
                CompletedExerciseOrm.id == result_id,
                CompletedExerciseOrm.exercise_structure_id == exercise_id,
                CompletedExerciseOrm.user_id == user_id,
            )
            .options(selectinload(CompletedExerciseOrm.filled_field))
        )
        return result.scalars().first()

    async def create_completed_exercise(
        self, completed: CompletedExerciseOrm, filled_fields: list[FilledFieldOrm]
    ) -> CompletedExerciseOrm:
        self.session.add(completed)
        await self.session.flush()

        for filled_field in filled_fields:
            self.session.add(filled_field)

        await self.session.flush()
        return completed
