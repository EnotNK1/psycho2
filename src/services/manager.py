import uuid
from typing import Dict, Any, Optional
from fastapi import status
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.models.clients import ClientsOrm, TasksOrm
from src.repositories.tests import logger
from src.schemas.task import Task
from src.services.base import BaseService
from src.exceptions import ObjectNotFoundException
from src.schemas.users import UpdateUserRequest, UpdateManagerRequest


class ManagerService(BaseService):
    async def become_manager(self, user_id: str, data: dict):
        user = await self.db.users.get_one_or_none(id=user_id)
        if not user:
            raise ObjectNotFoundException("User not found")

        # Обновляем данные пользователя и назначаем роль менеджера
        update_data = {
            "username": data.get("username"),
            "description": data.get("description"),
            "city": data.get("city"),
            "company": data.get("company"),
            "online": data.get("online"),
            "gender": data.get("gender"),
            "birth_date": data.get("birth_date"),
            "is_active": data.get("is_active"),
            "department": data.get("department"),
            "job_title": data.get("job_title"),
            "face_to_face": data.get("face_to_face"),
            "role_id": 2  # Предположим, что роль менеджера имеет id = 2
        }

        # Используем новую схему для обновления данных
        await self.db.users.edit(UpdateManagerRequest(**update_data), exclude_unset=True, id=user_id)
        await self.db.commit()

    async def get_all_manager(self):
        # Используем get_all с фильтром по role_id=2
        managers = await self.db.users.get_filtered(role_id=2)
        return managers

    async def create_task_for_clients(
            self,
            text: str,
            test_id: uuid.UUID,
            mentor_id: uuid.UUID,
            client_ids: Optional[list[uuid.UUID]] = None
    ):
        try:
            # Если список клиентов не передан, получаем всех привязанных клиентов
            if client_ids is None:
                relations = await self.db.clients.get_filtered(
                    mentor_id=mentor_id,
                    status=True
                )
                client_ids = [rel.client_id for rel in relations]

                if not client_ids:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="У вас нет привязанных клиентов"
                    )

            # Проверяем, что все клиенты привязаны к этому ментору
            invalid_clients = []
            for client_id in client_ids:
                relation = await self.db.clients.get_one_or_none(
                    client_id=client_id,
                    mentor_id=mentor_id,
                    status=True
                )
                if not relation:
                    invalid_clients.append(str(client_id))

            if invalid_clients:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Клиенты не привязаны к вам: {', '.join(invalid_clients)}"
                )

            # Получаем название теста (если нужно)
            test_title = None
            if test_id:
                test = await self.db.tests.get_one(id=test_id)
                test_title = test.title if test else None

            # Создаем задачи для каждого клиента
            created_tasks = []
            for client_id in client_ids:
                task_id = uuid.uuid4()
                task = TasksOrm(
                    id=task_id,
                    text=text,
                    test_title=test_title,
                    test_id=test_id,
                    mentor_id=mentor_id,
                    client_id=client_id,
                    is_complete=False
                )
                self.db.session.add(task)
                created_tasks.append(task)

            await self.db.session.commit()

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
                for task in created_tasks
            ]

        except HTTPException:
            await self.db.session.rollback()
            raise
        except Exception as e:
            await self.db.session.rollback()
            logger.error(f"Ошибка создания задач: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Произошла ошибка при создании задач"
            )

    async def get_mentor_tasks(self, mentor_id: uuid.UUID) -> list[Task]:
        try:
            # Получаем задачи из базы данных
            tasks = await self.db.tasks.get_filtered(mentor_id=mentor_id)

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
            logger.error(f"Ошибка при получении задач ментора: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Произошла ошибка при получении задач"
            )