from datetime import datetime, date
from http.client import HTTPException
from typing import Optional

from fastapi import Query
from fastapi import APIRouter

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
    InvalidTimestampHTTPException, MyAppException, MyAppHTTPException, DateHTTPException, DateException
)
from src.schemas.diary import DiaryDateRequestAdd
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.schemas.user_task import UserTaskRequestAdd, UserTaskRequestUpdate, UserTaskRequestDelete
from src.services.diary import DiaryService
from src.services.user_task import UserTaskService

router = APIRouter(prefix="/user-task", tags=["Задачи пользователя"])


@router.get("/actual", description="Если не передать day - возвращает все незавершенные задачи, если передать day - возвращает все незавершенные задачи + все задачи за переданный день")
async def get_actual_user_task(
    db: DBDep,
    user_id: UserIdDep,
    day: Optional[datetime] = None,
):
    try:
        return await UserTaskService(db).get_actual_user_tasks(user_id, day)
    except InvalidDateFormatError:
        raise InvalidDateFormatHTTPException
    except Exception as e:
        raise InternalErrorHTTPException

@router.get("/completed", description="Возвращает только выполненные задачи пользователя. Если даты переданы - задачи в границах дат. Если даты не переданы - задачи за последнюю неделю.")
async def get_completed_user_task(
    db: DBDep,
    user_id: UserIdDep,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    try:
        return await UserTaskService(db).get_completed_user_tasks(user_id, start_date, end_date)
    except DateException:
        raise DateHTTPException
    except InvalidDateFormatError:
        raise InvalidDateFormatHTTPException
    except Exception as e:
        raise InternalErrorHTTPException


@router.post("")
async def create_user_task(
    db: DBDep,
    user_id: UserIdDep,
    data: UserTaskRequestAdd
):
    try:
        await UserTaskService(db).add_user_task(data, user_id)
        return {"status": "OK"}
    except TextEmptyError:
        raise TextEmptyHTTPException
    except TextTooLongError:
        raise TextTooLongHTTPException
    except InvalidDateFormatError:
        raise InvalidDateFormatHTTPException
    except FutureDateError:
        raise FutureDateHTTPException
    except Exception as e:
        raise InternalErrorHTTPException

@router.patch("/update", description="Поля text и is_complete опциональные, можно передавать либо по одному, либо оба сразу")
async def update_user_task(
    db: DBDep,
    data: UserTaskRequestUpdate
):
    try:
        await UserTaskService(db).update_user_task(data)
        return {"status": "OK"}
    except TextEmptyError:
        raise TextEmptyHTTPException
    except TextTooLongError:
        raise TextTooLongHTTPException
    except InvalidDateFormatError:
        raise InvalidDateFormatHTTPException
    except FutureDateError:
        raise FutureDateHTTPException
    except Exception as e:
        raise InternalErrorHTTPException

@router.delete("")
async def delete_user_task(
    db: DBDep,
    data: UserTaskRequestDelete
):
    try:
        return await UserTaskService(db).delete(data)
    except InvalidTimestampError:
        raise InvalidTimestampHTTPException
    except Exception as e:
        raise InternalErrorHTTPException
