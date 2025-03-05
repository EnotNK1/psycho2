import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.dependencies.manager_id import ManagerIdDep
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.schemas.users import BecomeManagerRequest, GetAllManagerRequest, TaskRequest, GiveTaskListClientRequest, \
    GiveTaskAllClientRequest
from src.services.manager import ManagerService

router = APIRouter(prefix="/managers", tags=["Менеджер"])


@router.post("/become-manager")
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


@router.get("", summary="Получение всех менеджеров")
async def all_manager(
        db: DBDep
):
    return await ManagerService(db).get_all_manager()


@router.post("/task", summary="Дать задачу юзеру по user_id")
async def task(
        data: TaskRequest,
        mentor_id: ManagerIdDep,  # ID менеджера из токена
        db: DBDep
):
    return await ManagerService(db).task(mentor_id, data.model_dump())


@router.post("/tasks", summary="Дать задачу списку клиентов")
async def task_for_clients(
        data: GiveTaskListClientRequest,
        mentor_id: ManagerIdDep,  # ID менеджера из токена
        db: DBDep
):
    return await ManagerService(db).task_for_clients(mentor_id, data)


@router.post("/task-for-all-clients", summary="Дать задачу всем клиентам")
async def task_for_all_clients(
        data: GiveTaskAllClientRequest,
        mentor_id: ManagerIdDep,  # ID менеджера из токена
        db: DBDep
):
    return await ManagerService(db).task_for_all_clients(mentor_id, data)
