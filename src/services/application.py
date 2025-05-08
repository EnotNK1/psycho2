import logging
import uuid
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException

from src.exceptions import (
    ObjectNotFoundException,ObjectAlreadyExistsException, AccessDeniedHTTPException
)
from src.schemas.users import ClientSchema
from src.services.base import BaseService
from src.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatusUpdate, Application
)
logger = logging.getLogger(__name__)


class ApplicationService(BaseService):
    async def get_applications(self, manager_id: UUID) -> list[ApplicationResponse]:
        applications = await self.db.application.get_filtered(manager_id=manager_id)

        return [
            ApplicationResponse(
                id=app.id,
                client_id=app.client_id,
                manager_id=app.manager_id,
                status=app.status,
                text=app.text,
                inquiry=app.inquiry,
                created_at=app.created_at
            )
            for app in applications
        ]
              
    async def get_application(self, app_id: UUID) -> ApplicationResponse:


        applications = await self.db.application.get_filtered(id=app_id)

        if not applications:
            raise ObjectNotFoundException()

        # Берем первую (и единственную) заявку из списка
        application = applications[0]

        return ApplicationResponse(
            id=application.id,
            client_id=application.client_id,
            manager_id=application.manager_id,
            status=application.status,
            text=application.text,
            inquiry=application.inquiry,
            created_at=application.created_at
        )

    async def add_application(self, data: ApplicationCreate, user_id: int):
        if not await self.db.application.is_user_manager(data.manager_id):
            raise AccessDeniedHTTPException

        new_app_data = Application(
            id=uuid.uuid4(),
            manager_id=data.manager_id,
            client_id=user_id,
            text=data.text,
            inquiry=data.inquiry or [],
            status=False,
            created_at = datetime.now()
        )

        app_id = await self.db.application.add(new_app_data)
        await self.db.commit()
        return {"app_id": app_id}

    async def update_application_status(self, data: ApplicationStatusUpdate, manager_id: UUID):
        # Проверка прав менеджера
        if not await self.db.application.is_user_manager(manager_id):
            raise AccessDeniedHTTPException()

        # Получаем заявку
        applications = await self.db.application.get_filtered(id=data.app_id)
        if not applications:
            raise ObjectNotFoundException()
        application = applications[0]

        # Обновляем статус заявки
        application.status = data.status
        await self.db.application.edit(application, **{"id": data.app_id})
        await self.db.commit()

        # Логика для связи клиент-менеджер
        client_id = application.client_id
        logger.debug(f"Обработка связи для client_id={client_id}, mentor_id={manager_id}, status={data.status}")

        if data.status is True:
            # Создаем или активируем связь
            existing_relation = await self.db.clients.get_one_or_none(
                client_id=client_id,
                mentor_id=manager_id
            )

            if not existing_relation:
                logger.debug("Создание новой связи")
                new_client = ClientSchema(
                    id=uuid.uuid4(),
                    client_id=client_id,
                    mentor_id=manager_id,
                    text=application.text,
                    status=True
                )
                try:
                    await self.db.clients.add(new_client)
                    await self.db.commit()
                except ObjectAlreadyExistsException:
                    logger.debug("Связь уже существует, активируем")
                    await self.db.clients.edit(
                        data=ClientSchema(status=True),
                        client_id=client_id,
                        mentor_id=manager_id
                    )
                    await self.db.commit()
                except Exception as e:
                    logger.error(f"Ошибка при создании связи: {e}")
                    await self.db.rollback()
                    raise ObjectNotFoundException("Ошибка при создании связи")

        elif data.status is False:
            # Деактивируем или удаляем связь
            logger.debug("Попытка удаления связи")
            try:
                # В зависимости от вашей логики - либо delete, либо edit(status=False)
                await self.db.clients.delete(
                    client_id=client_id,
                    mentor_id=manager_id
                )
                # Или если нужно сохранить историю:
                # await self.db.clients.edit(
                #     data=ClientSchema(status=False),
                #     client_id=client_id,
                #     mentor_id=manager_id
                # )
                await self.db.commit()
            except Exception as e:
                logger.error(f"Ошибка при удалении связи: {e}")
                await self.db.rollback()
                raise ObjectNotFoundException("Ошибка при удалении связи")

        return {
            "status": "OK",
            "message": "Статус заявки обновлен",
        }
