import logging
import uuid

from fastapi import APIRouter, Depends
from typing import Optional, List
from fastapi import Query

from src.api.dependencies.admin import verify_admin
from src.api.dependencies.db import DBDep
from src.api.dependencies.pagination import PaginationDep
from src.api.dependencies.user_id import UserIdDep
from src.api.tests import should_add_relax
from src.exceptions import ObjectNotFoundException, ObjectNotFoundHTTPException
from src.schemas.psychologist import BecomePsychologistRequest, InquiryAddRequest
from src.schemas.task import TaskRequest
from src.services.psychologist import PsychologistService
from src.services.tests import TestService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/psychologist", tags=["Психолог"])


@router.patch("/become", summary="Стать психологом")
async def become_psychologist(
        db: DBDep,
        user_id: UserIdDep,
        data: BecomePsychologistRequest
):
    return await PsychologistService(db).become_psychologist(user_id, data)

@router.patch("/delete_profile", summary="Удалить анкету психолога")
async def delete_profile(
        db: DBDep,
        user_id: UserIdDep
):
    return await PsychologistService(db).delete_profile(user_id)

@router.post("/inquiry", summary="Добавить новый тэг")
async def inquiry_add(
        data: InquiryAddRequest,
        db: DBDep,
        user_id: uuid.UUID = Depends(verify_admin)
):
    return await PsychologistService(db).add_inquiry(data)

@router.get("/inquiry", summary="Получить список тегов")
async def inquiry_get(
        db: DBDep,
        user_id: UserIdDep
):
    return await PsychologistService(db).get_inquiry()

@router.delete("/inquiry/{inquiry_id}", summary="Удалить тег")
async def inquiry_delete(
        inquiry_id: int,
        db: DBDep,
        user_id: uuid.UUID = Depends(verify_admin)
):
    return await PsychologistService(db).delete_inquiry(inquiry_id)


@router.get("/{psychologist_id}", summary="Получить психолога по id")
async def get_psychologist(
        psychologist_id: uuid.UUID,
        db: DBDep
):
    return await PsychologistService(db).get_psychologist(psychologist_id)

@router.get("", summary="Получить всех психологов")
async def get_all_psychologists(
        db: DBDep,
        pagination: PaginationDep,
        inquiry_ids: Optional[List[int]] = Query(default=None),
):
    return await PsychologistService(db).get_all_psychologists(page=pagination.page, per_page=pagination.per_page, inquiry_ids=inquiry_ids)

@router.get("/clients/{client_id}/test-results", summary="Получить список тестов, пройденных клиентом")
async def client_tests_get(
        db: DBDep,
        user_id: UserIdDep,
        client_id: uuid.UUID
):
    return await PsychologistService(db).get_short_client_test_results(client_id=client_id, psychologist_id=user_id)

@router.get("/clients/{client_id}/tests/{test_id}/results",
            description="""
    Возвращает результат по test_id и client_id
    """,
            summary="Получение результатов теста по test_id и client_id")
async def result_by_user_and_test(
        db: DBDep,
        current_user_id: UserIdDep,
        test_id: uuid.UUID,
        client_id: uuid.UUID,
):
    try:
        test_service = TestService(db)
        res = await test_service.get_test_result_by_user_and_test(test_id, client_id, current_user_id)

        test_id_str = str(test_id)

        # res - это список результатов
        for item in res:
            scales = item.get("scale_results", [])
            add_relax = should_add_relax(test_id_str, scales)
            item["tags"] = ["relax"] if add_relax else []

        return res
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException

# @router.post("/task-for-clients", summary="Создать задачу для клиентов")
# async def create_task_for_clients(
#         task_data: TaskRequest,
#         db: DBDep,
#         mentor_id: UserIdDep
# ):
#     return await PsychologistService(db).create_task_for_clients(
#         text=task_data.text,
#         test_id=task_data.test_id,
#         mentor_id=mentor_id,
#         client_ids=task_data.client_ids
#     )


# @router.get("/clients/{client_id}/test-results", summary="Получение результата тестов клиента по client_id")
# async def get_client_test_results(
#     client_id: uuid.UUID,
#     psychologist_id: UserIdDep,
#     db: DBDep
# ):
#     return await PsychologistService(db).get_client_test_results(client_id, psychologist_id)
