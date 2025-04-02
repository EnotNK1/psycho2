from uuid import UUID
from src.exceptions import (
    InsufficientPermissionsException,
    ManagerNotFoundException,
    ApplicationNotFoundException, ObjectNotFoundException, ApplicationForUserNotFound, UserNotFoundException
)
from src.services.base import BaseService
from src.schemas.application import (
    ApplicationCreate,
    ApplicationShortResponse,
    ApplicationFullResponse,
    ApplicationStatusUpdate
)


class ApplicationService(BaseService):
    async def get_applications(self, manager_id: UUID):
        if not await self._is_manager(manager_id):
            raise InsufficientPermissionsException

        applications = await self.db.application.get_raw_applications_for_manager(manager_id)

        return [
            ApplicationShortResponse(
                app_id=app.id,
                client_id=app.client_id,
                username=await self._get_username(app.client_id),
                text=app.text,
                online=app.online,
                problem_id=app.problem_id,
                problem=app.problem
            )
            for app in applications
        ]


    async def get_application(self, app_id: UUID, manager_id: UUID):
        if not await self._is_manager(manager_id):
            raise InsufficientPermissionsException

        application = await self.db.application.get_raw_application_details(app_id)
        if not application:
            raise ApplicationNotFoundException

        user = await self.db.users.get_one_or_none(id=application.client_id)
        if not user:
            raise ApplicationNotFoundException("User not found")

        return ApplicationFullResponse(
            app_id=application.id,
            client_id=application.client_id,
            is_active=application.is_active,
            username=user.username,
            birth_date=user.birth_date,
            gender=user.gender or "unknown",
            text=application.text
        )


    async def create_application(self, data: ApplicationCreate, client_id: UUID):
        if not await self._is_manager(data.user_id):
            raise ManagerNotFoundException

        app_id = await self.db.application.create_application(
            client_id=client_id,
            manager_id=data.user_id,
            text=data.text
        )
        return {"app_id": app_id}


    async def update_application_status(self, data: ApplicationStatusUpdate, manager_id: UUID):
        try:
            if not await self._is_manager(manager_id):
                raise InsufficientPermissionsException("У вас недостаточно прав")

            updated = await self.db.application.update_application_status(
                client_id=data.user_id,
                status=data.status
            )

            if not updated:
                raise ApplicationForUserNotFound("Заявка не найдена или не принадлежит пользователю")

            return {"status": "OK", "message": "Статус обновлен"}
        except UserNotFoundException as e:
            raise UserNotFoundException(str(e))
        except ApplicationForUserNotFound as e:
            raise ApplicationForUserNotFound(str(e))
        except Exception as e:
            raise ApplicationNotFoundException(f"Системная ошибка: {str(e)}")


    async def _is_manager(self, user_id: UUID) -> bool:
        return await self.db.application.is_user_manager(user_id)


    async def _get_username(self, user_id: UUID) -> str:
        user = await self.db.users.get_one_or_none(id=user_id)
        return user.username if user else "Unknown"