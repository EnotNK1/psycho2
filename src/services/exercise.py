from typing import List, Optional
import logging
import uuid
import json
from fastapi import HTTPException, status
from src.services.base import BaseService
from src.schemas.exercise import (
    ExerciseResponse, ExerciseDetailResponse, ExerciseDetail1Response, ExerciseResultsResponse,
    FieldResponse, VariantResponse, CompletedExerciseCreate, ExerciseViewResponse, ResultDetailResponse,
    ExerciseCreate, FieldCreate, VariantCreate, ExerciseViewCreate, CompletedExerciseResponse, ExerciseAutoCreate, FieldAutoCreate
)
from src.exceptions import ObjectNotFoundHTTPException, MyAppException, ObjectAlreadyExistsException

logger = logging.getLogger(__name__)


class ExerciseService(BaseService):

    async def add_exercises(self, exercises_data):
        exercises = [ExerciseAutoCreate.model_validate(
            exercise) for exercise in exercises_data]
        created, skipped = 0, 0

        for exercise in exercises:
            try:
                existing_exercise = await self.db.exercise.get_one_or_none(id=exercise.id)
                if existing_exercise:
                    skipped += 1
                else:
                    await self.db.exercise.add(exercise)
                    created += 1
            except ObjectAlreadyExistsException:
                skipped += 1
            except Exception as ex:
                logger.error(f"Ошибка при добавлении упражнения: {ex}")
                await self.db.rollback()
                raise MyAppException()

        if created > 0:
            logger.info(f"{created} Упражнений успешно добавлено.")
        elif skipped > 0:
            logger.info("Все упражнения уже существуют в базе.")
        else:
            logger.info("Файл тестов пустой, ничего не добавлено.")

    async def add_fields(self, fields_data):
        fields = [FieldAutoCreate.model_validate(
            exercise) for exercise in fields_data]
        created, skipped = 0, 0

        for field in fields:
            try:
                if not field.exercise_structure_id:
                    continue
                existing_exercise = await self.db.exercise.get_one_or_none(id=field.exercise_structure_id)
                if not existing_exercise:
                    continue

                existing_field = await self.db.field.get_one_or_none(id=field.id)
                if existing_field:
                    skipped += 1
                else:
                    await self.db.field.add(field)
                    created += 1
            except ObjectAlreadyExistsException:
                skipped += 1
            except Exception as ex:
                logger.error(f"Ошибка при добавлении поля: {ex}")
                await self.db.rollback()
                raise MyAppException()

        if created > 0:
            logger.info(f"{created} Полей успешно добавлено.")
        elif skipped > 0:
            logger.info("Все поля уже существуют в базе.")
        else:
            logger.info("Файл тестов пустой, ничего не добавлено.")

    async def add_views(self, views_data):
        pass

    async def auto_create(self):
        try:
            with open("src/services/info/exercise_info.json", encoding="utf-8") as file:
                exercises_data = json.load(file)
            await self.add_exercises(exercises_data)

            with open("src/services/info/fields_info.json", encoding="utf-8") as file:
                scales_data = json.load(file)
            await self.add_fields(scales_data)

            # with open("src/services/info/views_info.json", encoding="utf-8") as file:
            #     answer_choices_data = json.load(file)
            # await self.add_views(answer_choices_data)

            await self.db.commit()
            return {"status": "OK", "message": "Упражнения, поля успешно созданы"}

        except Exception as ex:
            logger.error(f"Ошибка при автоматическом создании данных: {ex}")
            await self.db.rollback()
            raise MyAppException()

    async def create_exercise(self, exercise_data: ExerciseCreate) -> ExerciseResponse:
        return await self.db.exercise.create_exercise(exercise_data)

    async def create_field(self, exercise_id: uuid.UUID, field_data: FieldCreate) -> FieldResponse:
        if not await self.db.exercise.exercise_exists(exercise_id):
            raise ObjectNotFoundHTTPException
        return await self.db.exercise.create_field(exercise_id, field_data)

    async def create_variant(self, field_id: uuid.UUID, variant_data: VariantCreate) -> VariantResponse:
        field = await self.db.exercise.get_field(field_id)
        if not field:
            raise ObjectNotFoundHTTPException
        return await self.db.exercise.create_variant(field_id, variant_data)

    async def create_exercise_view(self, exercise_id: uuid.UUID, view_data: ExerciseViewCreate) -> ExerciseViewResponse:
        if not await self.db.exercise.exercise_exists(exercise_id):
            raise ObjectNotFoundHTTPException
        return await self.db.exercise.create_exercise_view(exercise_id, view_data)

    async def delete_exercise(self, exercise_id: uuid.UUID) -> None:
        if not await self.db.exercise.exercise_exists(exercise_id):
            raise ObjectNotFoundHTTPException
        await self.db.exercise.delete_exercise(exercise_id)

    async def delete_field(self, field_id: uuid.UUID) -> None:
        field = await self.db.exercise.get_field(field_id)
        if not field:
            raise ObjectNotFoundHTTPException
        await self.db.exercise.delete_field(field_id)

    async def delete_variant(self, variant_id: uuid.UUID) -> None:
        variant = await self.db.exercise.get_variant(variant_id)
        if not variant:
            raise ObjectNotFoundHTTPException
        await self.db.exercise.delete_variant(variant_id)

    async def delete_exercise_view(self, view_id: uuid.UUID) -> None:
        view = await self.db.exercise.get_exercise_view(view_id)
        if not view:
            raise ObjectNotFoundHTTPException
        await self.db.exercise.delete_exercise_view(view_id)

    async def get_all_exercises(self, user_id: Optional[uuid.UUID] = None) -> List[ExerciseResponse]:
        return await self.db.exercise.get_all_exercises(user_id)

    async def get_exercise_by_id(self, exercise_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> ExerciseDetailResponse:
        exercise = await self.db.exercise.get_exercise(exercise_id, user_id)
        if not exercise:
            raise ObjectNotFoundHTTPException
        return exercise

    async def get_exercise_structure_by_id(self, exercise_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> ExerciseDetail1Response:
        exercise = await self.db.exercise.get_exercise_strucuture(exercise_id, user_id)
        if not exercise:
            raise ObjectNotFoundHTTPException
        return exercise

    async def get_exercise_results(self, exercise_id: uuid.UUID, user_id: uuid.UUID) -> ExerciseResultsResponse:
        return await self.db.exercise.get_exercise_results(exercise_id, user_id)

    async def get_exercise_result_detail(self, exercise_id: uuid.UUID, result_id: uuid.UUID, user_id: uuid.UUID) -> ResultDetailResponse:
        result = await self.db.exercise.get_exercise_result_detail(exercise_id, result_id, user_id)
        if not result:
            raise ObjectNotFoundHTTPException
        return result

    async def complete_exercise(self, user_id: uuid.UUID, completed_data: CompletedExerciseCreate) -> CompletedExerciseResponse:
        try:
            return await self.db.exercise.complete_exercise(user_id, completed_data)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error completing exercise: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
