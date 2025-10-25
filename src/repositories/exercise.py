from typing import List, Optional
import datetime
import uuid
from src import enums
from sqlalchemy import select, and_, update, exists
from sqlalchemy.orm import joinedload, selectinload
from src.models.exercise import (
    ExerciseStructureOrm, FieldOrm, VariantOrm,
    CompletedExerciseOrm, FilledFieldOrm, ExerciseViewOrm
)
from src.schemas.exercise import (
    ExerciseCreate, ExerciseResponse, ExerciseDetailResponse, ExerciseDetail1Response, ExerciseResultsResponse, ResultSectionResponse,
    FieldResponse, VariantResponse, FieldCreate, VariantCreate, SectionResponse, CompletedExerciseResponse, ResultDetailResponse,
    CompletedExerciseCreate, PulledFieldResponse, PageResponse, ExerciseViewCreate, ExerciseViewResponse, ResultResponse
)
from src.repositories.base import BaseRepository


class ExerciseRepository(BaseRepository):
    async def create_exercise(self, exercise_data: ExerciseCreate) -> ExerciseResponse:
        exercise = ExerciseStructureOrm(
            id=uuid.uuid4(),
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
            title=field_data.title,
            major=field_data.major,
            view=field_data.view.value,
            type=field_data.type.value,
            placeholder=field_data.placeholder,
            prompt=field_data.prompt,
            description=field_data.description,
            order=field_data.order,
            exercises=exercises,
            variants=[]
        )
        self.session.add(field)
        await self.session.commit()
        await self.session.refresh(field)

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
            exercises=field.exercises,
            exercise_structure_id=field.exercise_structure_id,
            variants=[]
        )

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

    async def create_exercise_view(self, exercise_id: uuid.UUID, view_data: ExerciseViewCreate) -> ExerciseViewResponse:
        view = ExerciseViewOrm(
            id=uuid.uuid4(),
            exercise_structure_id=exercise_id,
            **view_data.model_dump()
        )
        self.session.add(view)
        await self.session.commit()
        await self.session.refresh(view)
        return ExerciseViewResponse.model_validate(view)

    async def delete_exercise(self, exercise_id: uuid.UUID) -> None:
        exercise = await self.session.get(ExerciseStructureOrm, exercise_id)
        if not exercise:
            raise ValueError("Exercise not found")

        await self.session.delete(exercise)
        await self.session.commit()

    async def delete_field(self, field_id: uuid.UUID) -> None:
        field = await self.session.get(FieldOrm, field_id)
        if not field:
            raise ValueError("Field not found")

        await self.session.delete(field)
        await self.session.commit()

    async def delete_variant(self, variant_id: uuid.UUID) -> None:
        variant = await self.session.get(VariantOrm, variant_id)
        if not variant:
            raise ValueError("Variant not found")

        await self.session.delete(variant)
        await self.session.commit()

    async def delete_exercise_view(self, view_id: uuid.UUID) -> None:
        view = await self.session.get(ExerciseViewOrm, view_id)
        if not view:
            raise ValueError("Exercise view not found")

        await self.session.delete(view)
        await self.session.commit()

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

    async def get_variant(self, variant_id: uuid.UUID) -> Optional[VariantOrm]:
        result = await self.session.execute(
            select(VariantOrm)
            .where(VariantOrm.id == variant_id)
        )
        return result.scalars().first()

    async def get_exercise_view(self, view_id: uuid.UUID) -> Optional[ExerciseViewOrm]:
        result = await self.session.execute(
            select(ExerciseViewOrm)
            .where(ExerciseViewOrm.id == view_id)
        )
        return result.scalars().first()

    async def get_all_exercises(self, user_id: Optional[uuid.UUID] = None) -> List[ExerciseResponse]:
        query = select(ExerciseStructureOrm)
        result = await self.session.execute(query)
        exercises = result.scalars().all()

        response = []
        for exercise in exercises:
            exercise_resp = ExerciseResponse.model_validate(exercise)

            if user_id:
                # Первое упражнение всегда доступно
                if exercise.linked_exercise_id is None:
                    exercise_resp.open = True
                else:
                    # Проверяем выполнено ли предыдущее упражнение
                    prev_completed = await self.session.scalar(
                        select(CompletedExerciseOrm)
                        .where(and_(
                            CompletedExerciseOrm.exercise_structure_id == exercise.linked_exercise_id,
                            CompletedExerciseOrm.user_id == user_id
                        ))
                    )
                    exercise_resp.open = prev_completed is not None
            else:
                # Без user_id все упражнения закрыты
                exercise_resp.open = False

            response.append(exercise_resp)

        return response

    async def get_exercise(self, exercise_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> ExerciseDetailResponse:
        exercise = await self.session.execute(
            select(ExerciseStructureOrm)
            .where(ExerciseStructureOrm.id == exercise_id)
        )
        exercise = exercise.scalars().unique().first()

        if not exercise:
            return None

        # Определяем доступность упражнения
        open_status = False
        if user_id:
            # Первое упражнение всегда доступно
            if exercise.linked_exercise_id is None:
                open_status = True
            else:
                # Проверяем выполнено ли предыдущее упражнение
                prev_completed = await self.session.scalar(
                    select(CompletedExerciseOrm)
                    .where(and_(
                        CompletedExerciseOrm.exercise_structure_id == exercise.linked_exercise_id,
                        CompletedExerciseOrm.user_id == user_id
                    ))
                )
                open_status = prev_completed is not None

        # Создаем ответ с новой структурой
        exercise_resp = ExerciseDetailResponse(
            id=exercise.id,
            title=exercise.title,
            picture_link=exercise.picture_link,
            description=exercise.description,
            time_to_read=exercise.time_to_read,
            questions_count=exercise.questions_count,
            open=open_status
        )
        return exercise_resp

    async def get_exercise_strucuture(self, exercise_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> ExerciseDetail1Response:
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
            raise ValueError("Exercise not found")

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
                title=field.title,
                text=field.text,
                source_exercise_id=completed_exercise.exercise_structure_id
            )
            for field, completed_exercise in pulled_fields_query
        ]

        # Группируем поля по страницам (order)
        fields_by_page = {}
        for field in exercise.field:
            page_number = field.order
            if page_number not in fields_by_page:
                fields_by_page[page_number] = []

            # Преобразуем Field в Section
            section = SectionResponse(
                id=field.id,
                title=field.title,
                view=field.view,
                type=field.type,
                placeholder=field.placeholder,
                prompt=field.prompt,
                variants=[
                    VariantResponse(
                        id=variant.id,
                        title=variant.title,
                        field_id=variant.field_id
                    ) for variant in field.variants
                ]
            )
            fields_by_page[page_number].append(section)

        # Создаем массив страниц
        pages = []
        for page_number, sections in sorted(fields_by_page.items()):
            page = PageResponse(
                page_number=page_number,
                sections=sections
            )
            pages.append(page)

        # Определяем доступность упражнения
        open_status = False
        if user_id:
            # Первое упражнение всегда доступно
            if exercise.linked_exercise_id is None:
                open_status = True
            else:
                # Проверяем выполнено ли предыдущее упражнение
                prev_completed = await self.session.scalar(
                    select(CompletedExerciseOrm)
                    .where(and_(
                        CompletedExerciseOrm.exercise_structure_id == exercise.linked_exercise_id,
                        CompletedExerciseOrm.user_id == user_id
                    ))
                )
                open_status = prev_completed is not None

        # Создаем ответ с новой структурой
        exercise_resp = ExerciseDetail1Response(
            id=exercise.id,
            title=exercise.title,
            picture_link=exercise.picture_link,
            description=exercise.description,
            time_to_read=exercise.time_to_read,
            questions_count=exercise.questions_count,
            open=open_status,
            pulled_fields=pulled_fields,
            pages=pages
        )

        return exercise_resp

    async def get_exercise_results(self, exercise_id: uuid.UUID, user_id: uuid.UUID) -> ExerciseResultsResponse:
        # Получаем все завершенные упражнения пользователя для данного exercise_id
        completed_exercises = await self.session.execute(
            select(CompletedExerciseOrm)
            .where(
                CompletedExerciseOrm.exercise_structure_id == exercise_id,
                CompletedExerciseOrm.user_id == user_id
            )
            .options(joinedload(CompletedExerciseOrm.filled_field))
            .order_by(CompletedExerciseOrm.date.desc())
        )
        completed_exercises = completed_exercises.scalars().unique().all()

        results = []
        for completed in completed_exercises:
            # Находим главное поле (preview) - первое поле или поле с major=True
            preview_text = "Нет данных"

            if completed.filled_field:
                # Ищем поле с major=True или берем первое поле
                major_field = next((ff for ff in completed.filled_field
                                    if hasattr(ff, 'major') and ff.major), None)

                if major_field:
                    preview_text = major_field.text
                else:
                    # Берем текст из первого заполненного поля
                    preview_text = completed.filled_field[0].text

            # Создаем результат
            result = ResultResponse(
                id=completed.id,
                exercise_id=completed.exercise_structure_id,
                date=completed.date.date(),  # преобразуем datetime в date
                preview=preview_text
            )
            results.append(result)

        return ExerciseResultsResponse(results=results)

    async def get_exercise_result_detail(self, exercise_id: uuid.UUID, result_id: uuid.UUID, user_id: uuid.UUID) -> ResultDetailResponse:
        # Используем join вместо selectinload
        completed_exercise_with_fields = await self.session.execute(
            select(CompletedExerciseOrm, FilledFieldOrm, FieldOrm)
            .join(FilledFieldOrm, CompletedExerciseOrm.id == FilledFieldOrm.completed_exercise_id)
            .join(FieldOrm, FilledFieldOrm.field_id == FieldOrm.id)
            .where(
                CompletedExerciseOrm.id == result_id,
                CompletedExerciseOrm.exercise_structure_id == exercise_id,
                CompletedExerciseOrm.user_id == user_id
            )
            .order_by(FieldOrm.order)  # сортируем по порядку полей
        )

        results = completed_exercise_with_fields.all()

        if not results:
            return None

        # Группируем результаты по completed_exercise
        completed_exercise = None
        sections = []

        for completed, filled_field, field in results:
            if not completed_exercise:
                completed_exercise = completed

            # Определяем значение в зависимости от типа поля
            value = filled_field.text
            if field.type == enums.FieldType.ADDABLE_LIST:
                try:
                    import json
                    value = json.loads(
                        filled_field.text) if filled_field.text else []
                except (json.JSONDecodeError, TypeError):
                    value = [filled_field.text] if filled_field.text else []

            section = ResultSectionResponse(
                title=field.title,
                view=field.view,
                type=field.type,
                value=value
            )
            sections.append(section)

        exercise = await self.session.execute(
            select(ExerciseStructureOrm)
            .where(ExerciseStructureOrm.id == exercise_id)
        )
        exercise = exercise.scalars().unique().first()

        if not exercise:
            return None

        return ResultDetailResponse(
            id=completed_exercise.id,
            title=exercise.title,
            picture_link=exercise.picture_link,
            description=exercise.description,
            exercise_id=completed_exercise.exercise_structure_id,
            date=completed_exercise.date.date(),
            sections=sections
        )

    async def complete_exercise(self, user_id: uuid.UUID, completed_data: CompletedExerciseCreate) -> CompletedExerciseResponse:
        # Получаем упражнение с явной загрузкой полей
        exercise = await self.session.execute(
            select(ExerciseStructureOrm)
            .where(ExerciseStructureOrm.id == completed_data.exercise_structure_id)
            .options(joinedload(ExerciseStructureOrm.field))
        )
        exercise = exercise.scalars().unique().first()

        if not exercise:
            raise ValueError("Exercise not found")

        # ПРОВЕРКА ДОСТУПНОСТИ УПРАЖНЕНИЯ
        if exercise.linked_exercise_id is not None:
            # Проверяем выполнено ли предыдущее упражнение
            prev_completed = await self.session.scalar(
                select(CompletedExerciseOrm)
                .where(and_(
                    CompletedExerciseOrm.exercise_structure_id == exercise.linked_exercise_id,
                    CompletedExerciseOrm.user_id == user_id
                ))
            )
            if prev_completed is None:
                raise ValueError(
                    "Cannot complete this exercise. Previous exercise must be completed first.")

        # Создаем запись о выполненном упражнении
        completed = CompletedExerciseOrm(
            id=uuid.uuid4(),
            user_id=user_id,
            exercise_structure_id=completed_data.exercise_structure_id,
            date=datetime.datetime.now()
        )
        self.session.add(completed)
        await self.session.flush()

        # Создаем заполненные поля
        for field_data in completed_data.filled_fields:
            field = await self.session.get(FieldOrm, field_data.field_id)
            if not field:
                raise ValueError(
                    f"Field with id {field_data.field_id} not found")

            filled_field = FilledFieldOrm(
                id=uuid.uuid4(),
                title=field.title,
                view=field.view,
                type=field.type,
                text=field_data.text,
                field_id=field_data.field_id,
                completed_exercise_id=completed.id,
                exercises=field.exercises
            )
            self.session.add(filled_field)

        await self.session.commit()

        # Формируем ответ:
        exercise_view = await self.session.execute(
            select(ExerciseViewOrm)
            .where(ExerciseViewOrm.exercise_structure_id == completed_data.exercise_structure_id)
            .order_by(ExerciseViewOrm.score.desc())
            .limit(1)
        )
        exercise_view = exercise_view.scalars().first()

        score = 10
        view = "blue"  # значение по умолчанию
        success_message = f"Поздравляем! Вы успешно прошли упражнение '{exercise.title}'"
        picture_link = exercise.picture_link  # значение по умолчанию

        if exercise_view:
            if exercise_view.view:
                view = exercise_view.view
            if exercise_view.score is not None and exercise_view.score != 0:
                score = exercise_view.score
            if hasattr(exercise_view, 'message') and exercise_view.message:
                success_message = exercise_view.message
            if hasattr(exercise_view, 'picture_link') and exercise_view.picture_link:
                picture_link = exercise_view.picture_link

        # Создаем ответ
        return CompletedExerciseResponse(
            id=completed.id,
            score=score,
            picture_link=picture_link,
            view=view,
            success_message=success_message
        )
