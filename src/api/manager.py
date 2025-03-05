from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.schemas.users import BecomeManagerRequest, GetAllManagerRequest
from src.services.manager import ManagerService

router = APIRouter(prefix="/manager", tags=["Менеджер"])


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

@router.get("", summary="Получение всех менеджеров", response_model=list[GetAllManagerRequest])
async def all_manager(
    db: DBDep
):
    return await ManagerService(db).all_manager()