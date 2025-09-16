# daily_tasks/router.py
import uuid
from fastapi import APIRouter, Cookie, Depends
from src.api.dependencies.db import DBDep
from src.api.dependencies.user_id import UserIdDep
from src.schemas.daily_tasks import DailyTaskId
from src.services.daily_tasks import DailyTaskService

router = APIRouter(prefix="/daily_tasks", tags=["Ежедневные задания"])

@router.get("", summary="Получение всех ежедневных заданий пользователя")
async def get_daily_tasks(
    db: DBDep,
    user_id: UserIdDep
):
    return await DailyTaskService(db).get_daily_tasks(user_id)

@router.patch("/complete", summary="Отметить ежедневное задание как выполненное")
async def complete_daily_task(
    data: DailyTaskId,
    db: DBDep,
    user_id: UserIdDep
):
    return await DailyTaskService(db).complete_daily_task(data, user_id)

@router.post("/refresh", summary="Обновить ежедневные задания (админская функция)")
async def refresh_daily_tasks(
    db: DBDep,
    user_id: UserIdDep
):
    return await DailyTaskService(db).refresh_daily_tasks(user_id)