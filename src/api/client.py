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

@router.patch("/complete-task", summary="Отметить задачу как выполненную")
async def complete_task(
    task_id: uuid.UUID,
    db: DBDep,
    client_id: UserIdDep
):
    return await ClientService(db).complete_task(task_id, client_id)