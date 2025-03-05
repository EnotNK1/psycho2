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
        managers = await self.db.users.get_filtered(role_id=2)
        result = []
        for manager in managers:
            manager_data = manager.__dict__
            # Убедимся, что все поля присутствуют
            manager_data.setdefault("company", None)
            manager_data.setdefault("online", None)
            manager_data.setdefault("description", None)
            manager_data.setdefault("is_active", None)
            manager_data.setdefault("department", None)
            manager_data.setdefault("face_to_face", None)
            result.append(GetAllManagerRequest(**manager_data))
        return result

    async def task(self, mentor_id: str, data: Dict[str, Any]):
        # Проверяем, существует ли пользователь
        user = await self.db.users.get_one_or_none(id=data.get("user_id"))
        if not user:
            raise ObjectNotFoundException("User not found")

        # Проверяем, существует ли менеджер
        manager = await self.db.users.get_one_or_none(id=mentor_id)
        if not manager:
            raise ObjectNotFoundException("Manager not found")

        # Получаем тест по test_id
        test = await self.db.tests.get_one(data.get("test_id"))  # Исправленный вызов
        if not test:
            raise ObjectNotFoundException("Test not found")

        # Создаем запись задачи
        task_data = {
            "id": uuid.uuid4(),  # Используем uuid.uuid4() для генерации UUID
            "text": data.get("text"),
            "test_title": test.title,  # Используем title из полученного теста
            "test_id": data.get("test_id"),
            "mentor_id": mentor_id,
            "client_id": data.get("user_id"),
            "is_complete": False
        }
        task = await self.db.tasks.create(**task_data)

        # Создаем запись клиента
        client_data = {
            "id": uuid.uuid4(),  # Генерация UUID
            "client_id": data.get("user_id"),
            "mentor_id": mentor_id,
            "text": data.get("text"),
            "status": False
        }
        await self.db.clients.create(**client_data)

        # Сохраняем изменения в базе данных
        await self.db.commit()

        return {"status": "OK", "message": "Task created successfully", "task_id": task.id}

    async def task_for_clients(self, mentor_id: str, data: GiveTaskListClientRequest):
        # Проверяем, существует ли менеджер
        manager = await self.db.users.get_one_or_none(id=mentor_id)
        if not manager:
            raise ObjectNotFoundException("Manager not found")

        # Получаем тест по test_id
        test = await self.db.tests.get_one(data.test_id)
        if not test:
            raise ObjectNotFoundException("Test not found")

        # Создаем задачи для каждого клиента
        task_ids = []
        for client_id in data.list_client:
            # Проверяем, существует ли клиент
            client = await self.db.users.get_one_or_none(id=client_id)
            if not client:
                logger.warning(f"Клиент с id={client_id} не найден. Пропускаем.")
                continue

            # Создаем запись задачи
            task_data = {
                "id": uuid.uuid4(),  # Генерация UUID
                "text": data.text,
                "test_title": test.title,  # Используем title из полученного теста
                "test_id": data.test_id,
                "mentor_id": mentor_id,
                "client_id": client_id,
                "is_complete": False
            }
            task = await self.db.tasks.create(**task_data)

            # Создаем запись клиента
            client_data = {
                "id": uuid.uuid4(),  # Генерация UUID
                "client_id": client_id,
                "mentor_id": mentor_id,
                "text": data.text,
                "status": False
            }
            await self.db.clients.create(**client_data)

            task_ids.append(task.id)

        # Сохраняем изменения в базе данных
        await self.db.commit()

        return {"status": "OK", "message": "Tasks created successfully", "task_ids": task_ids}

    async def task_for_all_clients(self, mentor_id: str, data: GiveTaskAllClientRequest):
        # Проверяем, существует ли менеджер
        manager = await self.db.users.get_one_or_none(id=mentor_id)
        if not manager:
            raise ObjectNotFoundException("Manager not found")

        # Получаем тест по test_id
        test = await self.db.tests.get_one(data.test_id)
        if not test:
            raise ObjectNotFoundException("Test not found")

        # Получаем всех клиентов из таблицы clients
        clients = await self.db.clients.get_all()
        if not clients:
            raise ObjectNotFoundException("No clients found")

        # Создаем задачи для каждого клиента
        task_ids = []
        for client in clients:
            # Создаем запись задачи
            task_data = {
                "id": uuid.uuid4(),  # Генерация UUID
                "text": data.text,
                "test_title": test.title,  # Используем title из полученного теста
                "test_id": data.test_id,
                "mentor_id": mentor_id,
                "client_id": client.client_id,  # Используем client_id из таблицы clients
                "is_complete": False
            }
            task = await self.db.tasks.create(**task_data)

            # Создаем запись клиента (если нужно)
            client_data = {
                "id": uuid.uuid4(),  # Генерация UUID
                "client_id": client.client_id,
                "mentor_id": mentor_id,
                "text": data.text,
                "status": False
            }
            await self.db.clients.create(**client_data)

            task_ids.append(task.id)

        # Сохраняем изменения в базе данных
        await self.db.commit()

        return {"status": "OK", "message": "Tasks created successfully for all clients", "task_ids": task_ids}
