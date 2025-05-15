import logging
import uuid
from typing import Optional, Dict, Any

from fastapi import HTTPException
from fastapi import status
from src.exceptions import ObjectNotFoundException, MyAppException
from src.models.clients import TasksOrm
from src.schemas.client import ClientGet
from src.schemas.task import Task
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class ClientService(BaseService):

    async def get_client(self, mentor_id: uuid.UUID, client_id: uuid.UUID | None = None):
        try:
            if client_id is None:
                # Получаем всех клиентов, связанных с этим ментором
                relations = await self.db.clients.get_filtered(mentor_id=mentor_id, status=True)

                if not relations:
                    return []

                # Получаем информацию о клиентах
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
                # Проверяем, что клиент привязан к этому ментору
                relation = await self.db.clients.get_one_or_none(
                    client_id=client_id,
                    mentor_id=mentor_id,
                    status=True
                )

                if not relation:
                    raise ObjectNotFoundException("Клиент не найден или не привязан к вам")

                # Получаем информацию о клиенте
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

    async def get_my_mentor(self, client_id: uuid.UUID) -> dict:
        try:
            # 1. Находим активную связь клиент-ментор
            relation = await self.db.clients.get_one_or_none(
                client_id=client_id,
                status=True
            )

            if not relation:
                raise HTTPException(
                    status_code=404,
                    detail="У вас нет назначенного ментора"
                )

            # 2. Получаем данные ментора
            mentor = await self.db.users.get_one(id=relation.mentor_id)
            if not mentor:
                raise HTTPException(
                    status_code=404,
                    detail="Ментор не найден в системе"
                )

            # 3. Получаем заявки клиента к этому ментору
            applications = await self.db.application.get_filtered(
                client_id=client_id,
                manager_id=mentor.id
            )

            # 4. Собираем все inquiry из заявок
            inquiry_list = []
            for app in applications:
                if app.inquiry:  # Проверяем, что inquiry не пустой
                    inquiry_list.extend(app.inquiry)

            # Удаляем дубликаты, если нужно
            unique_inquiry = list(set(inquiry_list)) if inquiry_list else []

            # 5. Формируем ответ
            return {
                "id": mentor.id,
                "username": mentor.username,
                "is_active": mentor.is_active,
                "inquiry": unique_inquiry  # Возвращаем уникальные inquiry
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении ментора: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Произошла ошибка при получении информации о менторе"
            )


    async def get_client_tasks(self, client_id: uuid.UUID) -> list[Task]:
        try:
            # Получаем задачи из базы данных
            tasks = await self.db.tasks.get_filtered(client_id=client_id)

            # Преобразуем ORM-модели в Pydantic-схемы
            return [
                Task(
                    id=task.id,
                    text=task.text,
                    test_title=task.test_title,
                    test_id=task.test_id,
                    mentor_id=task.mentor_id,
                    client_id=task.client_id,
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