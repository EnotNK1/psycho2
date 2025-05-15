import uuid
from email.policy import default

from fastapi import APIRouter, Cookie, Query

from typing import List, Optional

from src.api.dependencies.db import DBDep
from src.api.dependencies.user_id import UserIdDep
from src.schemas.task import Task, TaskRequest
from src.services.client import ClientService

router = APIRouter(prefix="/client", tags=["Клиент"])

@router.get("", summary="Получение всех клиентов или клиента по client_id"
)
async def get_client(
    db: DBDep,
    mentor_id: UserIdDep,
    client_id: uuid.UUID | None  = Query(default=None, description="ID клиента (опционально)")
):
    return await ClientService(db).get_client(mentor_id, client_id)

@router.get("/my-psychologist", summary="Получить информацию о своем менторе")
async def get_my_mentor(
    db: DBDep,
    client_id: UserIdDep
):
    return await ClientService(db).get_my_mentor(client_id)

@router.get("/my-tasks", summary="Получить все свои задачи")
async def get_my_tasks(
    db: DBDep,
    client_id: UserIdDep
):
    return await ClientService(db).get_client_tasks(client_id)
# @router.get(
#     "/psychologist/get_list_client",
#     tags=["Client"],
#     response_model=List[ResponseGetListClient],
# )
# def get_list_client(access_token: str = Cookie(None)):
#     return client_service.get_list_client(access_token)

# @router.get(
#     "/client/get_tasks",
#     tags=["Client"],
#     response_model=List[ResponseGetTask],
# )
# def get_tasks(access_token: str = Cookie(None)):
#     return client_service.get_tasks(access_token)

# @router.get(
#     "/client/get_given_tasks",
#     tags=["Client"],
#     response_model=List[ResponseGetTask],
# )
# def get_given_tasks(access_token: str = Cookie(None)):
#     return client_service.get_given_tasks(access_token)
#
# @router.post(
#     "/client/complete_task",
#     tags=["Client"],
#     response_model=None,
# )
# def complete_task(data: TaskId, access_token: str = Cookie(None)):
#     return client_service.complete_task(data, access_token)
#
# @router.delete(
#     "/client/delete_task",
#     tags=["Client"],
#     response_model=None,
# )
# def delete_task(data: TaskId, access_token: str = Cookie(None)):
#     return client_service.delete_task(data, access_token)
#
# @router.delete(
#     "/client/delete_incorrect_tasks",
#     tags=["Client"],
#     response_model=None,
# )
# def delete_incorrect_tasks(access_token: str = Cookie(None)):
#     return client_service.delete_incorrect_tasks(access_token)
#
# @router.post(
#     "/client/unfulfilled_task",
#     tags=["Client"],
#     response_model=None,
# )
# def unfulfilled_task(data: TaskId, access_token: str = Cookie(None)):
#     return client_service.unfulfilled_task(data, access_token)
#
# @router.get(
#     "/client/get_your_psychologist",
#     tags=["Client"],
#     response_model=List[ResponseGetPsychologist],
# )
# def get_your_psychologist(access_token: str = Cookie(None)):
#     return client_service.get_your_psychologist(access_token)