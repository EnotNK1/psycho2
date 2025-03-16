import uuid
from typing import Dict, Any

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.models.clients import ClientsOrm, TasksOrm
from src.repositories.tests import logger
from src.services.base import BaseService
from src.exceptions import ObjectNotFoundException
from src.schemas.users import UpdateUserRequest, UpdateManagerRequest, GetAllManagerRequest, GiveTaskListClientRequest, \
    GiveTaskAllClientRequest


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
            "face_to_face": data.get("face_to_face"),
            "role_id": 2  # Предположим, что роль менеджера имеет id = 2
        }

        # Используем новую схему для обновления данных
        await self.db.users.edit(UpdateManagerRequest(**update_data), exclude_unset=True, id=user_id)
        await self.db.commit()

    async def get_all_manager(self):
        # Используем get_all с фильтром по role_id=2
        managers = await self.db.users.get_all_by_filter(role_id=2)
        return managers

    async def task(self, mentor_id: str, data: Dict[str, Any]):

        user = await self.db.users.get_one_or_none(id=data.get("user_id"))
        if not user:
            raise ObjectNotFoundException("User not found")

        manager = await self.db.users.get_one_or_none(id=mentor_id)
        if not manager:
            raise ObjectNotFoundException("Manager not found")

        test = await self.db.tests.get_one(data.get("test_id"))
        if not test:
            raise ObjectNotFoundException("Test not found")

        task_data = {
            "id": uuid.uuid4(),
            "text": data.get("text"),
            "test_title": test.title,
            "test_id": data.get("test_id"),
            "mentor_id": mentor_id,
            "client_id": data.get("user_id"),
            "is_complete": False
        }
        task = await self.db.tasks.create(**task_data)

        client_data = {
            "id": uuid.uuid4(),
            "client_id": data.get("user_id"),
            "mentor_id": mentor_id,
            "text": data.get("text"),
            "status": True
        }
        await self.db.clients.create(**client_data)
        await self.db.commit()

        return {"status": "OK", "message": "Task created successfully", "task_id": task.id}

    async def task_for_clients(self, mentor_id: str, data: GiveTaskListClientRequest):

        manager = await self.db.users.get_one_or_none(id=mentor_id)
        if not manager:
            raise ObjectNotFoundException("Manager not found")
        test = await self.db.tests.get_one(data.test_id)
        if not test:
            raise ObjectNotFoundException("Test not found")

        task_ids = []
        for client_id in data.list_client:
            client = await self.db.users.get_one_or_none(id=client_id)
            if not client:
                logger.warning(f"Клиент с id={client_id} не найден. Пропускаем.")
                continue

            task_data = {
                "id": uuid.uuid4(),
                "text": data.text,
                "test_title": test.title,
                "test_id": data.test_id,
                "mentor_id": mentor_id,
                "client_id": client_id,
                "is_complete": False
            }
            task = await self.db.tasks.create(**task_data)

            client_data = {
                "id": uuid.uuid4(),
                "client_id": client_id,
                "mentor_id": mentor_id,
                "text": data.text,
                "status": True
            }
            await self.db.clients.create(**client_data)

            task_ids.append(task.id)
        await self.db.commit()

        return {"status": "OK", "message": "Tasks created successfully", "task_ids": task_ids}

    async def task_for_all_clients(self, mentor_id: str, data: GiveTaskAllClientRequest):
        manager = await self.db.users.get_one_or_none(id=mentor_id)
        if not manager:
            raise ObjectNotFoundException("Manager not found")

        test = await self.db.tests.get_one(data.test_id)
        if not test:
            raise ObjectNotFoundException("Test not found")

        clients = await self.db.clients.get_all_by_filter(status=True)
        logger.info(f"Найдено клиентов: {len(clients)}")
        if not clients:
            logger.warning("Клиенты с status=True не найдены")

        task_ids = []
        for client in clients:
            task_data = {
                "id": uuid.uuid4(),
                "text": data.text,
                "test_title": test.title,
                "test_id": data.test_id,
                "mentor_id": mentor_id,
                "client_id": client.client_id,
                "is_complete": False
            }
            task = await self.db.tasks.create(**task_data)

            client_data = {
                "id": uuid.uuid4(),
                "client_id": client.client_id,
                "mentor_id": mentor_id,
                "text": data.text,
                "status": True
            }
            await self.db.clients.create(**client_data)

            task_ids.append(task.id)

        await self.db.commit()

        return {"status": "OK", "message": "Tasks created successfully for all clients", "task_ids": task_ids}
