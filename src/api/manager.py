import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.dependencies.manager_id import ManagerIdDep
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.schemas.task import TaskRequest
from src.schemas.users import BecomeManagerRequest, GetAllManagerRequest
from src.services.manager import ManagerService

router = APIRouter(prefix="/managers", tags=["Менеджер"])


@router.patch("/manager", summary="Стать менеджером")
async def become_manager(
        db: DBDep,
        user_id: UserIdDep,
        data: BecomeManagerRequest
):
    try:
        await ManagerService(db).become_manager(user_id, data.model_dump())
        return {"status": "OK", "message": "User data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", summary="Получение всех менеджеров", response_model=GetAllManagerRequest)
async def all_manager(
        db: DBDep
):
    return await ManagerService(db).get_all_manager()


@router.post("/task-for-clients", summary="Создать задачу для клиентов")
async def create_task_for_clients(
    task_data: TaskRequest,
    db: DBDep,
    mentor_id: UserIdDep
):
    return await ManagerService(db).create_task_for_clients(
        text=task_data.text,
        test_id=task_data.test_id,
        mentor_id=mentor_id,
        client_ids=task_data.client_ids
    )

@router.get("/my-assigned-tasks",
           summary="Получить все созданные задачи")
async def get_my_assigned_tasks(
    db: DBDep,
    mentor_id: UserIdDep
):
    return await ManagerService(db).get_mentor_tasks(mentor_id)