import logging
import uuid

from fastapi import APIRouter
from src.api.dependencies.db import DBDep
from src.api.dependencies.user_id import UserIdDep
from src.schemas.psychologist import BecomePsychologistRequest
from src.schemas.task import TaskRequest
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


@router.post("/task-for-clients", summary="Создать задачу для клиентов")
async def create_task_for_clients(
        task_data: TaskRequest,
        db: DBDep,
        mentor_id: UserIdDep
):
    return await PsychologistService(db).create_task_for_clients(
        text=task_data.text,
        test_id=task_data.test_id,
        mentor_id=mentor_id,
        client_ids=task_data.client_ids
    )


@router.get("/clients/{client_id}/test-results", summary="Получение результата тестов клиента по client_id")
async def get_client_test_results(
    client_id: uuid.UUID,
    psychologist_id: UserIdDep,
    db: DBDep
):
    return await PsychologistService(db).get_client_test_results(client_id, psychologist_id)
