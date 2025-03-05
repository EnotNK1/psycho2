from typing import Dict, Any

from src.repositories.tests import logger
from src.services.base import BaseService
from src.exceptions import ObjectNotFoundException
from src.schemas.users import UpdateUserRequest, UpdateManagerRequest, GetAllManagerRequest


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
            "role_id": 2  # Предположим, что роль менеджера имеет id = 2
        }


        # Используем новую схему для обновления данных
        await self.db.users.edit(UpdateManagerRequest(**update_data), exclude_unset=True, id=user_id)
        await self.db.commit()

    async def all_manager(self) -> list[GetAllManagerRequest]:
        """
        Получаем всех менеджеров и возвращаем их в формате GetAllManagerRequest.
        """
        try:
            managers = await self.db.users.get_filtered(role_id=2)
            print(managers)
            result = []
            for manager in managers:
                manager_data = GetAllManagerRequest(
                    username=manager.username,
                    description=manager.description if hasattr(manager, 'description') else None,
                    city=manager.city if hasattr(manager, 'city') else None,
                    company=manager.company if hasattr(manager, 'company') else None,
                    online=manager.online if hasattr(manager, 'online') else None,
                    gender=manager.gender if hasattr(manager, 'gender') else None,
                    birth_date=manager.birth_date if hasattr(manager, 'birth_date') else None,
                    is_active=manager.is_active if hasattr(manager, 'is_active') else None,
                    department=manager.department if hasattr(manager, 'department') else None,
                    phone_number=manager.phone_number if hasattr(manager, 'phone_number') else None,
                    face_to_face=manager.face_to_face if hasattr(manager, 'face_to_face') else None
                )
                result.append(manager_data)
            return result
        except Exception as ex:
            logger.error(f"Ошибка при получении списка менеджеров: {ex}")
            await self.db.rollback()
            return []