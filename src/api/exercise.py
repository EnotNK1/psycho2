from typing import List
import uuid
from fastapi import APIRouter, status
from src.schemas.exercise import (
    ExerciseResponse, ExerciseDetailResponse, ExerciseDetail1Response, ResultDetailResponse,
    FieldResponse, VariantResponse, ExerciseViewCreate, ExerciseResultsResponse,
    ExerciseCreate, ExerciseUpdate, FieldCreate, FieldUpdate, VariantCreate, VariantUpdate, ExerciseViewResponse, ExerciseViewUpdate,
    CompletedExerciseCreate, ExercisesListResponse, CompletedExerciseResponse, CompletedExercisesListResponse
)
from src.services.exercise import ExerciseService
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep

router = APIRouter(prefix="/exercises", tags=["Упражнения"])


@router.post(
    "/auto",
    summary="Автоматическое создание упражнений",
    description="Синхронизирует упражнения, поля, варианты и view из фикстуры. Существующие поля обновляются по UUID, чтобы не удалять сохраненные ответы пользователей.",
)
async def auto_create(
        db: DBDep,
        user_id: UserIdDep
):
    await ExerciseService(db).auto_create()
    return {"status": "OK"}


@router.post(
    "/",
    response_model=ExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать упражнение",
    description="Создает структуру упражнения без полей и вариантов. Поля добавляются отдельным запросом.",
)
async def create_exercise(
    exercise_data: ExerciseCreate,
    db: DBDep
):
    return await ExerciseService(db).create_exercise(exercise_data)


@router.patch(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Обновить упражнение",
    description="Частично обновляет основные данные упражнения: название, описание, порядок, группу и связь с предыдущим упражнением.",
)
async def update_exercise(
    exercise_id: uuid.UUID,
    exercise_data: ExerciseUpdate,
    db: DBDep
):
    return await ExerciseService(db).update_exercise(exercise_id, exercise_data)


@router.delete(
    "/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить упражнение",
    description="Удаляет упражнение вместе с его полями, вариантами, view и результатами прохождения.",
)
async def delete_exercise(
    exercise_id: uuid.UUID,
    db: DBDep
):
    await ExerciseService(db).delete_exercise(exercise_id)


@router.post(
    "/{exercise_id}/fields/",
    response_model=FieldResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить поле упражнения",
    description="Добавляет поле в упражнение. Через exercises можно указать следующие упражнения, куда ответ должен стягиваться.",
)
async def create_field(
    exercise_id: uuid.UUID,
    field_data: FieldCreate,
    db: DBDep
):
    return await ExerciseService(db).create_field(exercise_id, field_data)


@router.patch(
    "/fields/{field_id}",
    response_model=FieldResponse,
    summary="Обновить поле упражнения",
    description="Частично обновляет поле, включая порядок, тип, подсказки, major и настройки стягивания.",
)
async def update_field(
    field_id: uuid.UUID,
    field_data: FieldUpdate,
    db: DBDep
):
    return await ExerciseService(db).update_field(field_id, field_data)


@router.delete(
    "/fields/{field_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить поле упражнения",
    description="Удаляет поле и связанные варианты. Если у поля есть сохраненные ответы, они также будут удалены каскадно.",
)
async def delete_field(
    field_id: uuid.UUID,
    db: DBDep
):
    await ExerciseService(db).delete_field(field_id)


@router.post(
    "/fields/{field_id}/variants/",
    response_model=VariantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить вариант ответа",
    description="Добавляет вариант ответа к полю с выбором.",
)
async def create_variant(
    field_id: uuid.UUID,
    variant_data: VariantCreate,
    db: DBDep
):
    return await ExerciseService(db).create_variant(field_id, variant_data)


@router.patch(
    "/variants/{variant_id}",
    response_model=VariantResponse,
    summary="Обновить вариант ответа",
    description="Меняет текст варианта ответа.",
)
async def update_variant(
    variant_id: uuid.UUID,
    variant_data: VariantUpdate,
    db: DBDep
):
    return await ExerciseService(db).update_variant(variant_id, variant_data)


@router.delete(
    "/variants/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить вариант ответа",
    description="Удаляет вариант ответа у поля.",
)
async def delete_variant(
    variant_id: uuid.UUID,
    db: DBDep
):
    await ExerciseService(db).delete_variant(variant_id)


@router.post(
    "/{exercise_id}/views/",
    response_model=ExerciseViewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить view результата",
    description="Создает сообщение, картинку, цветовую схему и score, которые вернутся после прохождения упражнения.",
)
async def create_exercise_view(
    exercise_id: uuid.UUID,
    view_data: ExerciseViewCreate,
    db: DBDep
):
    return await ExerciseService(db).create_exercise_view(exercise_id, view_data)


@router.patch(
    "/views/{view_id}",
    response_model=ExerciseViewResponse,
    summary="Обновить view результата",
    description="Частично обновляет настройки ответа после прохождения упражнения.",
)
async def update_exercise_view(
    view_id: uuid.UUID,
    view_data: ExerciseViewUpdate,
    db: DBDep
):
    return await ExerciseService(db).update_exercise_view(view_id, view_data)


@router.delete(
    "/views/{view_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить view результата",
    description="Удаляет настройки ответа после прохождения упражнения.",
)
async def delete_exercise_view(
    view_id: uuid.UUID,
    db: DBDep
):
    await ExerciseService(db).delete_exercise_view(view_id)


@router.get(
    "/",
    response_model=ExercisesListResponse,
    summary="Получить список упражнений",
    description="Возвращает упражнения двумя массивами: regular_exercises для обычных и related_exercises для связанных. Поле open вычисляется для текущего пользователя.",
)
async def get_all_exercises(
    db: DBDep,
    user_id: UserIdDep = None
):
    exercises = await ExerciseService(db).get_all_exercises(user_id)
    return ExercisesListResponse(**exercises)


@router.get(
    "/passed/user/{user_id}",
    response_model=CompletedExercisesListResponse,
    summary="Получить пройденные упражнения пользователя",
    description="Административный вариант запроса: возвращает упражнения, которые проходил пользователь с указанным user_id.",
)
async def get_passed_exercises_by_user(
    user_id: uuid.UUID,
    db: DBDep
):
    exercises = await ExerciseService(db).get_passed_exercises_by_user(user_id)
    return CompletedExercisesListResponse(exercises=exercises)


@router.get(
    "/passed/user",
    response_model=CompletedExercisesListResponse,
    summary="Получить мои пройденные упражнения",
    description="Возвращает упражнения, которые проходил текущий авторизованный пользователь.",
)
async def get_passed_exercises(
    db: DBDep,
    user_id: UserIdDep
):
    exercises = await ExerciseService(db).get_passed_exercises_by_user(user_id)
    return CompletedExercisesListResponse(exercises=exercises)


@router.get(
    "/{exercise_id}",
    response_model=ExerciseDetailResponse,
    summary="Получить описание упражнения",
    description="Возвращает основную информацию об упражнении без полей. Для структуры полей используйте /structure.",
)
async def get_exercise(
    exercise_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep = None
):
    return await ExerciseService(db).get_exercise_by_id(exercise_id, user_id)


@router.get(
    "/{exercise_id}/structure",
    response_model=ExerciseDetail1Response,
    summary="Получить структуру упражнения",
    description="Возвращает страницы, поля, варианты ответа и pulled_fields — ответы из прошлых упражнений, доступные для стягивания.",
)
async def get_exercise_structure(
    exercise_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep = None
):
    return await ExerciseService(db).get_exercise_structure_by_id(exercise_id, user_id)


@router.get(
    "/{exercise_id}/results",
    response_model=ExerciseResultsResponse,
    summary="Получить мои результаты упражнения",
    description="Возвращает список прохождений текущего пользователя по упражнению. preview берется из major-поля, а если ответов нет, возвращается null.",
)
async def get_exercise_results(
    exercise_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep
):
    return await ExerciseService(db).get_exercise_results(exercise_id, user_id)


@router.get(
    "/{exercise_id}/results/user/{user_id}",
    response_model=ExerciseResultsResponse,
    summary="Получить результаты упражнения пользователя",
    description="Административный вариант запроса: возвращает список прохождений указанного пользователя по упражнению.",
)
async def get_exercise_results_by_user(
    exercise_id: uuid.UUID,
    user_id: uuid.UUID,
    db: DBDep
):
    return await ExerciseService(db).get_exercise_results(exercise_id, user_id)


@router.get(
    "/{exercise_id}/results/{result_id}",
    response_model=ResultDetailResponse,
    summary="Получить мой детальный результат",
    description="Возвращает конкретное прохождение упражнения с заполненными секциями. Если результат существует, но ответов в нем нет, sections будет пустым массивом.",
)
async def get_exercise_result_detail(
    exercise_id: uuid.UUID,
    result_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep
):
    return await ExerciseService(db).get_exercise_result_detail(exercise_id, result_id, user_id)


@router.get(
    "/{exercise_id}/results/{result_id}/user/{user_id}",
    response_model=ResultDetailResponse,
    summary="Получить детальный результат пользователя",
    description="Административный вариант запроса: возвращает конкретное прохождение указанного пользователя.",
)
async def get_exercise_result_detail_by_user(
    exercise_id: uuid.UUID,
    result_id: uuid.UUID,
    user_id: uuid.UUID,
    db: DBDep
):
    return await ExerciseService(db).get_exercise_result_detail(exercise_id, result_id, user_id)


@router.post(
    "/complete",
    response_model=CompletedExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Пройти упражнение",
    description="Создает результат прохождения. Нужно передать exercise_structure_id и ответы по filled_fields. Для стянутых полей указывайте pulled_completed_exercise_id и pulled_group_key.",
)
async def complete_exercise(
    completed_data: CompletedExerciseCreate,
    db: DBDep,
    user_id: UserIdDep
):
    return await ExerciseService(db).complete_exercise(user_id, completed_data)
