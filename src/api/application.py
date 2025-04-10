from fastapi import APIRouter, Depends
from uuid import UUID
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.schemas.application import (
    ApplicationCreate,
    ApplicationStatusUpdate
)
from src.services.application import ApplicationService
from src.exceptions import (
    InsufficientPermissionsHTTPException,
    ManagerNotFoundHTTPException,
    InsufficientPermissionsException,
    ObjectNotFoundException,
    ManagerNotFoundException,
    ForUserNotFoundException,
    ForUserNotFoundHTTPException,
    UserNotFoundException,
    UserNotFoundHTTPException,
    ObjectNotFoundHTTPException
)

router = APIRouter(prefix="/applications", tags=["Заявки"])


@router.get("")
async def get_applications(
    db: DBDep,
    user_id: UserIdDep
):
    try:
        return await ApplicationService(db).get_applications(user_id)
    except InsufficientPermissionsException:
        raise InsufficientPermissionsHTTPException


@router.get("/{app_id}")
async def get_application(
    app_id: UUID,
    db: DBDep,
    user_id: UserIdDep
):
    try:
        return await ApplicationService(db).get_application(app_id, user_id)
    except InsufficientPermissionsException:
        raise InsufficientPermissionsHTTPException
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.post("")
async def add_application(
    data: ApplicationCreate,
    db: DBDep,
    user_id: UserIdDep
):
    try:
        return await ApplicationService(db).add_application(data, user_id)
    except ManagerNotFoundException:
        raise ManagerNotFoundHTTPException


@router.post("/status")
async def update_application_status(
    data: ApplicationStatusUpdate,
    db: DBDep,
    user_id: UserIdDep
):
    try:
        return await ApplicationService(db).update_application_status(data, user_id)
    except InsufficientPermissionsException:
        raise InsufficientPermissionsHTTPException
    except UserNotFoundException:
        raise UserNotFoundHTTPException
    except ForUserNotFoundException:
        raise ForUserNotFoundHTTPException
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
