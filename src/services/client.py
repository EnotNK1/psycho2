import logging
import uuid
from typing import Optional, Dict, Any, List

from fastapi import HTTPException
from fastapi import status
from src.exceptions import ObjectNotFoundException, MyAppException
from src.models.clients import TasksOrm
from src.schemas.client import ClientGet
from src.schemas.task import Task, GetMyTask, TaskUpdate
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class ClientService(BaseService):

    async def get_client(self, mentor_id: uuid.UUID, client_id: uuid.UUID | None = None):
        try:
            if client_id is None:
                relations = await self.db.clients.get_filtered(mentor_id=mentor_id, status=True)

                if not relations:
                    return []

                clients = []
                for relation in relations:
                    client = await self.db.users.get_one_or_none(id=relation.client_id)
                    if client:
                        clients.append({
                            "id": client.id,
                            "username": client.username,
                            "birth_date": client.birth_date,
                            "text": relation.text,
                            "gender": client.gender,
                            "inquiry": []
                        })

                return clients
            else:

                relation = await self.db.clients.get_one_or_none(
                    client_id=client_id,
                    mentor_id=mentor_id,
                    status=True
                )

                if not relation:
                    raise ObjectNotFoundException("Клиент не найден или не привязан к вам")

                client = await self.db.users.get_one_or_none(id=client_id)
                if not client:
                    raise ObjectNotFoundException("Клиент не найден")

                return {
                    "id": client.id,
                    "username": client.username,
                    "birth_date": client.birth_date,
                    "text": relation.text,
                    "gender": client.gender,
                    "inquiry": []
                }

        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении клиента: {ex}")
            raise MyAppException()

    async def get_my_mentors(self, client_id: uuid.UUID) -> list[dict]:
        try:
            # Получаем все активные связи клиент-менеджер
            relations = await self.db.clients.get_filtered(
                client_id=client_id,
                status=True
            )

            if not relations:
                raise ObjectNotFoundException("No active mentor relations found")

            mentors_data = []

            for relation in relations:
                mentor = await self.db.users.get_one(id=relation.mentor_id)
                if not mentor:
                    continue

                applications = await self.db.application.get_filtered(
                    client_id=client_id,
                    manager_id=mentor.id
                )

                inquiry_list = []
                for app in applications:
                    if app.inquiry:
                        inquiry_list.extend(app.inquiry)

                unique_inquiry = list(set(inquiry_list)) if inquiry_list else []

                mentors_data.append({
                    "id": mentor.id,
                    "username": mentor.username,
                    "is_active": mentor.is_active,
                    "inquiry": unique_inquiry
                })

            if not mentors_data:
                raise ObjectNotFoundException("No valid mentors found")

            return mentors_data

        except ObjectNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении менторов: {str(e)}")
            raise MyAppException()


    async def get_client_tasks(self, client_id: uuid.UUID) -> list[GetMyTask]:
        try:

            tasks = await self.db.tasks.get_filtered(client_id=client_id)

            return [
                GetMyTask(
                    id=task.id,
                    text=task.text,
                    test_title=task.test_title,
                    test_id=task.test_id,
                    mentor_id=task.mentor_id,
                    is_complete=task.is_complete
                )
                for task in tasks
            ]

        except Exception as e:
            logger.error(f"Ошибка при получении задач: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Произошла ошибка при получении задач"
            )

    async def complete_task(self, task_id: uuid.UUID, client_id: uuid.UUID) -> dict:
        try:

            task = await self.db.tasks.get_one(id=task_id)
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Задача не найдена"
                )

            if str(task.client_id) != str(client_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Эта задача вам не принадлежит"
                )

            await self.db.tasks.edit(
                data=TaskUpdate(is_complete=not task.is_complete),
                id=task_id
            )
            await self.db.commit()

            return {
                "status": "success",
                "message": "Статус задачи изменён",
                "task_id": str(task_id)
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.db.session.rollback()
            logger.error(f"Ошибка при обновлении задачи: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Произошла ошибка при обновлении задачи"
            )