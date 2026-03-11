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

router = APIRouter(prefix="/ontology", tags=["Онтология"])


@router.get("")
async def get_ontology(
        db: DBDep,
        my_user_id: UserIdDep,
):
    return []
    # try:
    #     result = await AuthService(db).get_ontology(my_user_id)
    #
    #     return {"result": result}
    # except Exception as e:
    #     raise ObjectNotFoundHTTPException()