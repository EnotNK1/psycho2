from __future__ import annotations

import datetime
import json
import logging
import uuid
from typing import Optional

from fastapi import HTTPException, status

from src import enums
from src.exceptions import MyAppException, ObjectNotFoundHTTPException
from src.models.exercise import (
    CompletedExerciseOrm,
    ExerciseStructureOrm,
    ExerciseViewOrm,
    FieldOrm,
    FilledFieldOrm,
    VariantOrm,
)
from src.schemas.exercise import (
    CompletedExerciseCreate,
    CompletedExerciseItemResponse,
    CompletedExerciseResponse,
    ExerciseCreate,
    ExerciseDetail1Response,
    ExerciseDetailResponse,
    ExerciseResponse,
    ExerciseResultsResponse,
    ExerciseViewCreate,
    ExerciseViewUpdate,
    ExerciseViewResponse,
    FieldCreate,
    FieldUpdate,
    FieldResponse,
    PageResponse,
    PulledFieldItemResponse,
    PulledFieldResponse,
    ResultDetailResponse,
    ResultResponse,
    ResultSectionResponse,
    SectionResponse,
    VariantCreate,
    VariantUpdate,
    VariantResponse,
    ExerciseUpdate,
)
from src.services.base import BaseService
from src.services.fixtures.exercise import EXERCISES

logger = logging.getLogger(__name__)


class ExerciseService(BaseService):
    async def auto_create(self):
        try:
            await self.seed_exercises()
            await self.db.commit()
            return {"status": "OK", "message": "Упражнения и поля успешно созданы"}
        except Exception as ex:
            logger.error(f"Ошибка при автоматическом создании данных: {ex}")
            await self.db.rollback()
            raise MyAppException()

    async def seed_exercises(self):
        for exercise_data in EXERCISES:
            exercise_id = uuid.UUID(exercise_data["id"])
            existing = await self.db.exercise.get_exercise_entity(exercise_id)

            if existing:
                existing.title = exercise_data["title"]
                existing.description = exercise_data["description"]
                existing.picture_link = exercise_data["picture_link"]
                existing.time_to_read = exercise_data["time_to_read"]
                existing.questions_count = exercise_data["questions_count"]
                existing.sort_order = exercise_data["sort_order"]
                existing.group = exercise_data.get("group", 1)
                existing.linked_exercise_id = (
                    uuid.UUID(exercise_data["linked_exercise_id"])
                    if exercise_data.get("linked_exercise_id")
                    else None
                )
                exercise = await self.db.exercise.update_exercise(existing)
                await self.db.exercise.delete_fields_by_exercise(exercise_id)
                await self.db.exercise.delete_views_by_exercise(exercise_id)
            else:
                exercise = ExerciseStructureOrm(
                    id=exercise_id,
                    title=exercise_data["title"],
                    description=exercise_data["description"],
                    picture_link=exercise_data["picture_link"],
                    time_to_read=exercise_data["time_to_read"],
                    questions_count=exercise_data["questions_count"],
                    sort_order=exercise_data["sort_order"],
                    group=exercise_data.get("group", 1),
                    linked_exercise_id=(
                        uuid.UUID(exercise_data["linked_exercise_id"])
                        if exercise_data.get("linked_exercise_id")
                        else None
                    ),
                )
                await self.db.exercise.add(exercise)
                await self.db.exercise.flush()

            for field_data in exercise_data.get("fields", []):
                field = FieldOrm(
                    id=uuid.UUID(field_data["id"]),
                    title=field_data["title"],
                    major=field_data["major"],
                    view=field_data["view"],
                    type=field_data["type"],
                    placeholder=field_data.get("placeholder"),
                    prompt=field_data.get("prompt"),
                    description=field_data.get("description", ""),
                    order=field_data["order"],
                    position=field_data["position"],
                    pull_group=field_data.get("pull_group"),
                    exercise_structure_id=exercise_id,
                    exercises=field_data.get("exercises"),
                )
                await self.db.exercise.add(field)
                await self.db.exercise.flush()

                for variant_data in field_data.get("variants", []):
                    variant = VariantOrm(
                        id=uuid.UUID(variant_data["id"]),
                        field_id=field.id,
                        title=variant_data["title"],
                    )
                    await self.db.exercise.add(variant)

            for view_data in exercise_data.get("views", []):
                view = ExerciseViewOrm(
                    id=uuid.UUID(view_data["id"]),
                    exercise_structure_id=exercise_id,
                    view=view_data.get("view"),
                    score=view_data.get("score"),
                    picture_link=view_data.get("picture_link"),
                    message=view_data.get("message"),
                )
                await self.db.exercise.add(view)

        await self.db.exercise.flush()

    async def create_exercise(self, exercise_data: ExerciseCreate) -> ExerciseResponse:
        exercise = ExerciseStructureOrm(
            id=uuid.uuid4(), **exercise_data.model_dump())
        exercise = await self.db.exercise.create_exercise(exercise)
        await self.db.commit()
        return self._to_exercise_response(exercise, open_status=False)

    async def update_exercise(
        self, exercise_id: uuid.UUID, exercise_data: ExerciseUpdate
    ) -> ExerciseResponse:
        exercise = await self.db.exercise.get_exercise_entity(exercise_id)
        if not exercise:
            raise ObjectNotFoundHTTPException

        for field_name, value in exercise_data.model_dump(exclude_unset=True).items():
            setattr(exercise, field_name, value)

        exercise = await self.db.exercise.update_exercise(exercise)
        await self.db.commit()
        return self._to_exercise_response(exercise, open_status=False)

    async def create_field(self, exercise_id: uuid.UUID, field_data: FieldCreate) -> FieldResponse:
        exercise = await self.db.exercise.get_exercise_entity(exercise_id)
        if not exercise:
            raise ObjectNotFoundHTTPException

        field = FieldOrm(
            id=uuid.uuid4(),
            exercise_structure_id=exercise_id,
            title=field_data.title,
            major=field_data.major,
            view=field_data.view.value,
            type=field_data.type.value,
            placeholder=field_data.placeholder,
            prompt=field_data.prompt,
            description=field_data.description,
            order=field_data.order,
            position=field_data.position,
            pull_group=field_data.pull_group,
            exercises=[str(exercise_id)
                       for exercise_id in field_data.exercises]
            if field_data.exercises
            else None,
        )
        field = await self.db.exercise.create_field(field)
        await self.db.commit()
        return FieldResponse(
            id=field.id,
            title=field.title,
            major=field.major,
            view=field.view,
            type=field.type,
            placeholder=field.placeholder,
            prompt=field.prompt,
            description=field.description,
            order=field.order,
            position=field.position,
            pull_group=field.pull_group,
            exercises=field.exercises,
            exercise_structure_id=field.exercise_structure_id,
            variants=[],
        )

    async def update_field(self, field_id: uuid.UUID, field_data: FieldUpdate) -> FieldResponse:
        field = await self.db.exercise.get_field(field_id)
        if not field:
            raise ObjectNotFoundHTTPException

        for field_name, value in field_data.model_dump(exclude_unset=True).items():
            if field_name == "exercises" and value is not None:
                setattr(field, field_name, [str(exercise_id)
                        for exercise_id in value])
            elif field_name in {"view", "type"} and value is not None:
                setattr(field, field_name, value.value)
            else:
                setattr(field, field_name, value)

        field = await self.db.exercise.update_field(field)
        await self.db.commit()
        return self._to_field_response(field)

    async def create_variant(self, field_id: uuid.UUID, variant_data: VariantCreate) -> VariantResponse:
        field = await self.db.exercise.get_field(field_id)
        if not field:
            raise ObjectNotFoundHTTPException

        variant = VariantOrm(
            id=uuid.uuid4(), field_id=field_id, title=variant_data.title)
        variant = await self.db.exercise.create_variant(variant)
        await self.db.commit()
        return VariantResponse.model_validate(variant)

    async def update_variant(
        self, variant_id: uuid.UUID, variant_data: VariantUpdate
    ) -> VariantResponse:
        variant = await self.db.exercise.get_variant(variant_id)
        if not variant:
            raise ObjectNotFoundHTTPException

        for field_name, value in variant_data.model_dump(exclude_unset=True).items():
            setattr(variant, field_name, value)

        variant = await self.db.exercise.update_variant(variant)
        await self.db.commit()
        return VariantResponse.model_validate(variant)

    async def create_exercise_view(
        self, exercise_id: uuid.UUID, view_data: ExerciseViewCreate
    ) -> ExerciseViewResponse:
        exercise = await self.db.exercise.get_exercise_entity(exercise_id)
        if not exercise:
            raise ObjectNotFoundHTTPException

        view = ExerciseViewOrm(
            id=uuid.uuid4(),
            exercise_structure_id=exercise_id,
            **view_data.model_dump(),
        )
        view = await self.db.exercise.create_exercise_view(view)
        await self.db.commit()
        return ExerciseViewResponse.model_validate(view)

    async def update_exercise_view(
        self, view_id: uuid.UUID, view_data: ExerciseViewUpdate
    ) -> ExerciseViewResponse:
        view = await self.db.exercise.get_exercise_view(view_id)
        if not view:
            raise ObjectNotFoundHTTPException

        for field_name, value in view_data.model_dump(exclude_unset=True).items():
            setattr(view, field_name, value)

        view = await self.db.exercise.update_exercise_view(view)
        await self.db.commit()
        return ExerciseViewResponse.model_validate(view)

    async def delete_exercise(self, exercise_id: uuid.UUID) -> None:
        exercise = await self.db.exercise.get_exercise_entity(exercise_id)
        if not exercise:
            raise ObjectNotFoundHTTPException
        await self.db.exercise.delete_exercise(exercise)
        await self.db.commit()

    async def delete_field(self, field_id: uuid.UUID) -> None:
        field = await self.db.exercise.get_field(field_id)
        if not field:
            raise ObjectNotFoundHTTPException
        await self.db.exercise.delete_field(field)
        await self.db.commit()

    async def delete_variant(self, variant_id: uuid.UUID) -> None:
        variant = await self.db.exercise.get_variant(variant_id)
        if not variant:
            raise ObjectNotFoundHTTPException
        await self.db.exercise.delete_variant(variant)
        await self.db.commit()

    async def delete_exercise_view(self, view_id: uuid.UUID) -> None:
        view = await self.db.exercise.get_exercise_view(view_id)
        if not view:
            raise ObjectNotFoundHTTPException
        await self.db.exercise.delete_exercise_view(view)
        await self.db.commit()

    async def get_all_exercises(self, user_id: Optional[uuid.UUID] = None) -> dict[str, list[ExerciseResponse]]:
        exercises = await self.db.exercise.get_all_exercise_entities()
        open_map = await self._get_open_map(exercises, user_id)
        regular_exercises: list[ExerciseResponse] = []
        related_exercises: list[ExerciseResponse] = []
        for exercise in exercises:
            response = self._to_exercise_response(exercise, open_map[exercise.id])
            if exercise.group == 2:
                related_exercises.append(response)
            else:
                regular_exercises.append(response)
        return {
            "regular_exercises": regular_exercises,
            "related_exercises": related_exercises,
        }

    async def get_passed_exercises_by_user(
        self, user_id: uuid.UUID
    ) -> list[CompletedExerciseItemResponse]:
        rows = await self.db.exercise.get_passed_exercises_by_user(user_id)
        return [
            CompletedExerciseItemResponse(
                id=exercise_id,
                title=title,
                picture_link=picture_link,
                date=last_completed_at,
            )
            for exercise_id, title, picture_link, last_completed_at in rows
        ]

    async def get_exercise_by_id(
        self, exercise_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> ExerciseDetailResponse:
        exercise = await self.db.exercise.get_exercise_entity(exercise_id)
        if not exercise:
            raise ObjectNotFoundHTTPException
        return self._to_exercise_detail_response(
            exercise,
            await self._is_exercise_open(exercise, user_id),
        )

    async def get_exercise_structure_by_id(
        self, exercise_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> ExerciseDetail1Response:
        exercise = await self.db.exercise.get_exercise_with_fields(exercise_id)
        if not exercise:
            raise ObjectNotFoundHTTPException

        pulled_rows = await self.db.exercise.get_pulled_fields(exercise_id, user_id)
        return self._to_exercise_structure_response(
            exercise=exercise,
            open_status=await self._is_exercise_open(exercise, user_id),
            pulled_rows=pulled_rows,
        )

    async def get_exercise_results(
        self, exercise_id: uuid.UUID, user_id: uuid.UUID
    ) -> ExerciseResultsResponse:
        completed_exercises = await self.db.exercise.get_exercise_results(exercise_id, user_id)
        exercise = await self.db.exercise.get_exercise_with_fields(exercise_id)
        major_field_ids = {
            field.id for field in exercise.field
            if exercise is not None and field.major
        } if exercise else set()

        results = [
            ResultResponse(
                id=completed.id,
                exercise_id=completed.exercise_structure_id,
                date=completed.date.date(),
                preview=self._extract_preview(completed, major_field_ids),
            )
            for completed in completed_exercises
        ]
        return ExerciseResultsResponse(results=results)

    async def get_exercise_result_detail(
        self, exercise_id: uuid.UUID, result_id: uuid.UUID, user_id: uuid.UUID
    ) -> ResultDetailResponse:
        rows = await self.db.exercise.get_exercise_result_detail_rows(exercise_id, result_id, user_id)
        if not rows:
            raise ObjectNotFoundHTTPException

        exercise = await self.db.exercise.get_exercise_entity(exercise_id)
        if not exercise:
            raise ObjectNotFoundHTTPException

        completed = rows[0][0]
        sections = [
            ResultSectionResponse(
                title=field.title,
                view=field.view,
                type=field.type,
                value=self._normalize_filled_value(
                    field.type, filled_field.text),
                pulled_completed_exercise_id=filled_field.pulled_completed_exercise_id,
                pulled_group_key=filled_field.pulled_group_key,
                pulled_fields=self._build_snapshot_items(
                    filled_field.pulled_fields_snapshot
                ),
            )
            for _, filled_field, field in rows
        ]

        return ResultDetailResponse(
            id=completed.id,
            title=exercise.title,
            picture_link=exercise.picture_link,
            description=exercise.description,
            exercise_id=completed.exercise_structure_id,
            date=completed.date.date(),
            sections=sections,
        )

    async def complete_exercise(
        self, user_id: uuid.UUID, completed_data: CompletedExerciseCreate
    ) -> CompletedExerciseResponse:
        try:
            exercise = await self.db.exercise.get_exercise_with_fields(
                completed_data.exercise_structure_id
            )
            if not exercise:
                raise ValueError("Exercise not found")

            if not await self._is_exercise_open(exercise, user_id):
                raise ValueError(
                    "Cannot complete this exercise. Previous exercise must be completed first."
                )

            completed = CompletedExerciseOrm(
                id=uuid.uuid4(),
                user_id=user_id,
                exercise_structure_id=completed_data.exercise_structure_id,
                date=datetime.datetime.now(),
            )
            available_pulled_groups = self._index_pulled_groups(
                await self.db.exercise.get_pulled_fields(
                    completed_data.exercise_structure_id,
                    user_id,
                )
            )
            filled_fields = self._build_filled_fields(
                exercise=exercise,
                completed_id=completed.id,
                completed_data=completed_data,
                available_pulled_groups=available_pulled_groups,
            )
            await self.db.exercise.create_completed_exercise(completed, filled_fields)

            ontology_temp = await self.db.ontology_entry.get_filtered(user_id=user_id)
            for temp in ontology_temp:
                if temp.destination_id == completed_data.exercise_structure_id:
                    await self.db.ontology_entry.delete(
                        user_id=user_id,
                        destination_id=completed_data.exercise_structure_id,
                    )

            await self.db.commit()

            exercise_view = await self.db.exercise.get_latest_exercise_view(
                completed_data.exercise_structure_id
            )
            return self._build_completed_response(completed.id, exercise, exercise_view)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            logger.error(f"Error completing exercise: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def _get_open_map(
        self, exercises: list[ExerciseStructureOrm], user_id: Optional[uuid.UUID]
    ) -> dict[uuid.UUID, bool]:
        if user_id is None:
            return {exercise.id: False for exercise in exercises}

        linked_ids = [
            exercise.linked_exercise_id for exercise in exercises if exercise.linked_exercise_id]
        completed_ids = await self.db.exercise.get_completed_exercise_ids(user_id, linked_ids)

        return {
            exercise.id: exercise.linked_exercise_id is None
            or exercise.linked_exercise_id in completed_ids
            for exercise in exercises
        }

    async def _is_exercise_open(
        self, exercise: ExerciseStructureOrm, user_id: Optional[uuid.UUID]
    ) -> bool:
        if user_id is None:
            return False
        if exercise.linked_exercise_id is None:
            return True
        return await self.db.exercise.is_exercise_completed(exercise.linked_exercise_id, user_id)

    def _to_exercise_response(
        self, exercise: ExerciseStructureOrm, open_status: bool
    ) -> ExerciseResponse:
        return ExerciseResponse(
            id=exercise.id,
            title=exercise.title,
            picture_link=exercise.picture_link,
            sort_order=exercise.sort_order,
            group=exercise.group,
            open=open_status,
        )

    def _to_field_response(self, field: FieldOrm) -> FieldResponse:
        return FieldResponse(
            id=field.id,
            title=field.title,
            major=field.major,
            view=field.view,
            type=field.type,
            placeholder=field.placeholder,
            prompt=field.prompt,
            description=field.description,
            order=field.order,
            position=field.position,
            pull_group=field.pull_group,
            exercises=field.exercises,
            exercise_structure_id=field.exercise_structure_id,
            variants=[VariantResponse.model_validate(
                variant) for variant in field.variants],
        )

    def _to_exercise_detail_response(
        self, exercise: ExerciseStructureOrm, open_status: bool
    ) -> ExerciseDetailResponse:
        return ExerciseDetailResponse(
            id=exercise.id,
            title=exercise.title,
            picture_link=exercise.picture_link,
            description=exercise.description,
            time_to_read=exercise.time_to_read,
            questions_count=exercise.questions_count,
            sort_order=exercise.sort_order,
            group=exercise.group,
            open=open_status,
        )

    def _to_exercise_structure_response(
        self,
        exercise: ExerciseStructureOrm,
        open_status: bool,
        pulled_rows: list[tuple[FilledFieldOrm, CompletedExerciseOrm]],
    ) -> ExerciseDetail1Response:
        pages_map: dict[int, list[SectionResponse]] = {}
        for field in sorted(
            exercise.field,
            key=lambda item: (item.order, item.position,
                              item.title, str(item.id)),
        ):
            pages_map.setdefault(field.order, []).append(
                SectionResponse(
                    id=field.id,
                    title=field.title,
                    view=field.view,
                    type=field.type,
                    position=field.position,
                    placeholder=field.placeholder,
                    prompt=field.prompt,
                    variants=[VariantResponse.model_validate(
                        variant) for variant in field.variants],
                )
            )

        pages = [
            PageResponse(page_number=page_number, sections=sections)
            for page_number, sections in sorted(pages_map.items())
        ]
        pulled_fields = list(self._index_pulled_groups(pulled_rows).values())

        return ExerciseDetail1Response(
            id=exercise.id,
            title=exercise.title,
            picture_link=exercise.picture_link,
            description=exercise.description,
            time_to_read=exercise.time_to_read,
            questions_count=exercise.questions_count,
            sort_order=exercise.sort_order,
            group=exercise.group,
            open=open_status,
            pulled_fields=pulled_fields,
            pages=pages,
        )

    def _extract_preview(
        self, completed: CompletedExerciseOrm, major_field_ids: set[uuid.UUID]
    ):
        if not completed.filled_field:
            return "Нет данных"

        major_field = next(
            (
                filled_field
                for filled_field in completed.filled_field
                if filled_field.field_id in major_field_ids
            ),
            None,
        )
        preview_source = major_field or completed.filled_field[0]
        return preview_source.text

    def _normalize_filled_value(self, field_type: enums.FieldType | str, value):
        if field_type == enums.FieldType.ADDABLE_LIST or field_type == enums.FieldType.ADDABLE_LIST.value:
            if isinstance(value, list):
                return value
            if value in (None, ""):
                return []
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    return parsed if isinstance(parsed, list) else [parsed]
                except json.JSONDecodeError:
                    return [value]
        return value

    def _build_filled_fields(
        self,
        exercise: ExerciseStructureOrm,
        completed_id: uuid.UUID,
        completed_data: CompletedExerciseCreate,
        available_pulled_groups: dict[tuple[uuid.UUID, str], PulledFieldResponse],
    ) -> list[FilledFieldOrm]:
        fields_by_id = {field.id: field for field in exercise.field}
        expected_ids = set(fields_by_id)
        grouped_keys: dict[tuple[uuid.UUID | None, str | None], set[uuid.UUID]] = {}
        has_pulled_links = False

        filled_fields: list[FilledFieldOrm] = []
        for field_data in completed_data.filled_fields:
            field = fields_by_id.get(field_data.field_id)
            if field is None:
                raise ValueError(
                    f"Field with id {field_data.field_id} not found")

            self._validate_pulled_reference(field_data, available_pulled_groups)
            group_identity = (
                field_data.pulled_completed_exercise_id,
                field_data.pulled_group_key,
            )
            if group_identity[0] is not None:
                has_pulled_links = True
            grouped_keys.setdefault(group_identity, set())
            if field.id in grouped_keys[group_identity]:
                raise ValueError(
                    "Filled fields contain duplicates within the same pulled group."
                )
            grouped_keys[group_identity].add(field.id)

            pulled_snapshot = None
            if (
                field_data.pulled_completed_exercise_id is not None
                and field_data.pulled_group_key is not None
            ):
                pulled_snapshot = self._serialize_pulled_group(
                    available_pulled_groups[
                        (
                            field_data.pulled_completed_exercise_id,
                            field_data.pulled_group_key,
                        )
                    ]
                )

            filled_fields.append(
                FilledFieldOrm(
                    id=uuid.uuid4(),
                    title=field.title,
                    view=field.view,
                    type=field.type,
                    text=field_data.text,
                    field_id=field.id,
                    completed_exercise_id=completed_id,
                    exercises=field.exercises,
                    source_group_key=field.pull_group or str(field.id),
                    pulled_completed_exercise_id=field_data.pulled_completed_exercise_id,
                    pulled_group_key=field_data.pulled_group_key,
                    pulled_fields_snapshot=pulled_snapshot,
                )
            )

        if not has_pulled_links:
            provided_ids = [
                filled_field.field_id
                for filled_field in completed_data.filled_fields
            ]
            if len(provided_ids) != len(set(provided_ids)):
                raise ValueError("Filled fields contain duplicates.")
            if set(provided_ids) != expected_ids:
                raise ValueError("All exercise fields must be filled exactly once.")
        else:
            for group_field_ids in grouped_keys.values():
                if not group_field_ids.issubset(expected_ids):
                    raise ValueError("Filled fields contain unknown exercise fields.")

        return filled_fields

    def _index_pulled_groups(
        self,
        pulled_rows: list[tuple[FilledFieldOrm, CompletedExerciseOrm]],
    ) -> dict[tuple[uuid.UUID, str], PulledFieldResponse]:
        grouped: dict[tuple[uuid.UUID, str], PulledFieldResponse] = {}
        for filled_field, completed in pulled_rows:
            group_key = filled_field.source_group_key or str(filled_field.field_id)
            composite_key = (completed.id, group_key)
            group = grouped.get(composite_key)
            if group is None:
                group = PulledFieldResponse(
                    source_completed_exercise_id=completed.id,
                    source_exercise_id=completed.exercise_structure_id,
                    source_group_key=group_key,
                    fields=[],
                )
                grouped[composite_key] = group
            group.fields.append(
                PulledFieldItemResponse(
                    source_filled_field_id=filled_field.id,
                    field_id=filled_field.field_id,
                    title=filled_field.title,
                    text=filled_field.text,
                    source_group_key=group_key,
                )
            )
        return grouped

    def _validate_pulled_reference(
        self,
        field_data,
        available_pulled_groups: dict[tuple[uuid.UUID, str], PulledFieldResponse],
    ) -> None:
        has_completed = field_data.pulled_completed_exercise_id is not None
        has_group_key = field_data.pulled_group_key is not None
        if has_completed != has_group_key:
            raise ValueError(
                "Pulled field reference must include both pulled_completed_exercise_id and pulled_group_key."
            )
        if not has_completed:
            return
        group_identity = (
            field_data.pulled_completed_exercise_id,
            field_data.pulled_group_key,
        )
        if group_identity not in available_pulled_groups:
            raise ValueError("Pulled field group not found for this exercise.")

    def _serialize_pulled_group(
        self, pulled_group: PulledFieldResponse
    ) -> list[dict[str, object]]:
        return [
            {
                "source_filled_field_id": str(item.source_filled_field_id),
                "field_id": str(item.field_id),
                "title": item.title,
                "text": item.text,
                "source_group_key": item.source_group_key,
            }
            for item in pulled_group.fields
        ]

    def _build_snapshot_items(
        self, snapshot: object
    ) -> list[PulledFieldItemResponse]:
        if not isinstance(snapshot, list):
            return []

        items: list[PulledFieldItemResponse] = []
        for item in snapshot:
            if not isinstance(item, dict):
                continue
            items.append(
                PulledFieldItemResponse(
                    source_filled_field_id=item["source_filled_field_id"],
                    field_id=item["field_id"],
                    title=item["title"],
                    text=item.get("text"),
                    source_group_key=item["source_group_key"],
                )
            )
        return items

    def _build_completed_response(
        self,
        completed_id: uuid.UUID,
        exercise: ExerciseStructureOrm,
        exercise_view: Optional[ExerciseViewOrm],
    ) -> CompletedExerciseResponse:
        score = 10
        view = "blue"
        success_message = f"Поздравляем! Вы успешно прошли упражнение '{exercise.title}'"
        picture_link = exercise.picture_link

        if exercise_view:
            if exercise_view.view:
                view = exercise_view.view
            if exercise_view.score not in (None, 0):
                score = exercise_view.score
            if exercise_view.message:
                success_message = exercise_view.message
            if exercise_view.picture_link:
                picture_link = exercise_view.picture_link

        return CompletedExerciseResponse(
            id=completed_id,
            score=score,
            picture_link=picture_link,
            view=view,
            success_message=success_message,
        )
