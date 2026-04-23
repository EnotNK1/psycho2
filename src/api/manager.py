import uuid

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.api.dependencies.admin import verify_admin, verify_hrd
from src.api.dependencies.manager_id import ManagerIdDep
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.schemas.task import TaskRequest
from src.schemas.users import BecomeManagerRequest, BecomeHRDRequest, BecomeHRequest
from src.services.manager import ManagerService

router = APIRouter(prefix="/managers", tags=["Менеджер"])

@router.get("/hrd", summary="Получить список всех главных HR")
async def get_all_hrd(
        db: DBDep,
        user_id: uuid.UUID = Depends(verify_admin)
):
    try:
        return await ManagerService(db).get_all_hrd()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/hr", summary="Получить список всех HR")
async def get_all_hr(
        db: DBDep,
        user_id: uuid.UUID = Depends(verify_admin)
):
    try:
        return await ManagerService(db).get_all_hr()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/hrd", summary="Назначить главного HR")
async def create_hrd(
        data: BecomeHRDRequest,
        db: DBDep,
        user_id: uuid.UUID = Depends(verify_admin)
):
    try:
        await ManagerService(db).create_hdr(data)
        return {"status": "OK"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/hr", summary="Назначить HR")
async def create_hr(
        data: BecomeHRequest,
        db: DBDep,
        user_id: uuid.UUID = Depends(verify_hrd)
):
    try:
        await ManagerService(db).create_hr(data)
        return {"status": "OK"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# @router.patch("/manager", summary="Стать менеджером")
# async def become_manager(
#         db: DBDep,
#         user_id: UserIdDep,
#         data: BecomeManagerRequest
# ):
#     try:
#         await ManagerService(db).become_manager(user_id, data.model_dump())
#         return {"status": "OK", "message": "User data updated successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @router.get("", summary="Получение всех менеджеров")
# async def all_manager(
#         db: DBDep
# ):
#     return await ManagerService(db).get_all_manager()
#

# @router.post("/task-for-clients", summary="Создать задачу для клиентов")
# async def create_task_for_clients(
#     task_data: TaskRequest,
#     db: DBDep,
#     mentor_id: UserIdDep
# ):
#     return await ManagerService(db).create_task_for_clients(
#         text=task_data.text,
#         test_id=task_data.test_id,
#         mentor_id=mentor_id,
#         client_ids=task_data.client_ids
#     )
#
# @router.get("/my-assigned-tasks",
#            summary="Получить все созданные задачи")
# async def get_my_assigned_tasks(
#     db: DBDep,
#     mentor_id: UserIdDep
# ):
#     return await ManagerService(db).get_mentor_tasks(mentor_id)