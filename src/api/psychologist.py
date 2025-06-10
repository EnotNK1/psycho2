import logging
import uuid


from fastapi import APIRouter
from src.api.dependencies.db import DBDep
from src.api.dependencies.user_id import UserIdDep
from src.schemas.psychologist import BecomePsychologistRequest
from src.services.psychologist import PsychologistService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/psychologist", tags=["Психолог"])


@router.patch("/become", summary="Стать психологом")
async def become_psychologist(
    db: DBDep,
    user_id: UserIdDep,
    data: BecomePsychologistRequest
):
    return await PsychologistService(db).become_psychologist(user_id, data)


@router.get("/{psychologist_id}", summary="Получить психолога по id")
async def get_psychologist(
    psychologist_id: uuid.UUID,
    db: DBDep
):
    return await PsychologistService(db).get_psychologist(psychologist_id)


@router.get("/", summary="Получить всех психологов")
async def get_all_psychologists(
    db: DBDep
):
    return await PsychologistService(db).get_all_psychologists()