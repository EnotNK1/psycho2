import uuid

from fastapi import Query
from fastapi import APIRouter

from src.api.dependencies.pagination import PaginationDep
from src.exceptions import (
    InternalErrorHTTPException,
    FutureDateError,
    InvalidDateFormatError,
    TextTooLongError,
    TextEmptyError,
    InvalidDateFormatHTTPException,
    FutureDateHTTPException,
    TextTooLongHTTPException,
    TextEmptyHTTPException,
    InvalidTimestampError,
    InvalidTimestampHTTPException, ObjectNotFoundException, ObjectNotFoundHTTPException
)
from src.schemas.diary import DiaryDateRequestAdd, AbcDiaryAdd, AbcDiaryUpdate
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.services.abc_diary import AbcDiaryService
from src.services.diary import DiaryService

router = APIRouter(prefix="/abc_diary", tags=["ABC-дневник"])


@router.get(
    "",
    description="Получить список записей ABC-дневника текущего пользователя с пагинацией.",
)
async def get_my_abc_diary(
    db: DBDep,
    user_id: UserIdDep,
    pagination: PaginationDep,
):
    try:
        return await AbcDiaryService(db).get_user_entries(
            user_id=user_id,
            page=pagination.page,
            per_page=pagination.per_page,
        )
    except Exception:
        raise InternalErrorHTTPException


@router.post(
    "",
    description="Создать новую запись ABC-дневника.",
)
async def create_abc_diary(
    db: DBDep,
    user_id: UserIdDep,
    data: AbcDiaryAdd,
):
    try:
        return await AbcDiaryService(db).create_entry(data, user_id)
    except TextEmptyError:
        raise TextEmptyHTTPException
    except TextTooLongError:
        raise TextTooLongHTTPException
    except Exception:
        raise InternalErrorHTTPException


@router.get(
    "/{entry_id}",
    description="Получить детальную информацию о записи по ID.",
)
async def get_abc_diary_entry(
    db: DBDep,
    user_id: UserIdDep,
    entry_id: uuid.UUID,
):
    try:
        return await AbcDiaryService(db).get_entry(entry_id, user_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except Exception:
        raise InternalErrorHTTPException


@router.patch(
    "/{entry_id}",
    description="Частично обновить запись (только переданные поля).",
)
async def update_abc_diary_entry(
    db: DBDep,
    user_id: UserIdDep,
    entry_id: uuid.UUID,
    data: AbcDiaryUpdate,
):
    try:
        return await AbcDiaryService(db).update_entry(entry_id, user_id, data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except TextEmptyError:
        raise TextEmptyHTTPException
    except TextTooLongError:
        raise TextTooLongHTTPException
    except Exception:
        raise InternalErrorHTTPException


@router.delete(
    "/{entry_id}",
    description="Удалить запись по ID.",
)
async def delete_abc_diary_entry(
    db: DBDep,
    user_id: UserIdDep,
    entry_id: uuid.UUID,
):
    try:
        await AbcDiaryService(db).delete_entry(entry_id, user_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except Exception:
        raise InternalErrorHTTPException


# --------------------- Эндпоинты для психолога (получение записей клиентов) ---------------------

@router.get(
    "/clients/{client_id}",
    description="Психолог получает список записей ABC-дневника своего клиента.",
)
async def get_client_abc_diary(
    db: DBDep,
    pagination: PaginationDep,
    user_id: UserIdDep,
    client_id: uuid.UUID
):
    try:
        # Сервис проверит, что психолог имеет доступ к этому клиенту
        return await AbcDiaryService(db).get_client_entries(
            client_id=client_id,
            psychologist_id=user_id,
            page=pagination.page,
            per_page=pagination.per_page,
        )
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except Exception:
        raise InternalErrorHTTPException