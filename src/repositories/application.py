from os.path import exists
from uuid import UUID
from sqlalchemy import select, insert, update
from src.models.application import ApplicationOrm
from src.models.users import UsersOrm
from src.repositories.base import BaseRepository
from src.exceptions import ObjectNotFoundException, ApplicationForUserNotFound, UserNotFoundException


class ApplicationRepository(BaseRepository):
    model = ApplicationOrm

    async def get_raw_applications_for_manager(self, manager_id: UUID):
        query = select(self.model).where(self.model.manager_id == manager_id)
        result = await self.session.execute(query)
        return result.scalars().all()


    async def get_raw_application_details(self, app_id: UUID):
        query = select(self.model).where(self.model.id == app_id)
        result = await self.session.execute(query)
        return result.scalars().one_or_none()


    async def create_application(self, client_id: UUID, manager_id: UUID, text: str):
        data = {
            "client_id": client_id,
            "manager_id": manager_id,
            "text": text
        }
        result = await self.session.execute(
            insert(self.model).values(**data).returning(self.model))
        model = result.scalars().one()
        await self.session.commit()
        return model.id


    async def update_application_status(self, client_id: UUID, status: bool):
        try:
            user_exists = await self.session.scalar(
                select(1).where(UsersOrm.id == client_id)
            )
            if not user_exists:
                raise UserNotFoundException("Пользователь не найден")

            stmt = (
                update(self.model)
                .where(self.model.client_id == client_id)
                .values(is_active=status)
            )
            result = await self.session.execute(stmt)

            if result.rowcount == 0:
                raise ApplicationForUserNotFound("Заявка для пользователя не найдена")

            await self.session.commit()
            return True
        except (UserNotFoundException, ApplicationForUserNotFound):
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise ApplicationForUserNotFound(f"Ошибка при обновлении статуса: {str(e)}")


    async def is_user_manager(self, user_id: UUID) -> bool:
        query = select(UsersOrm.role_id).where(UsersOrm.id == user_id)
        result = await self.session.execute(query)
        role_id = result.scalar_one_or_none()
        return role_id == 3
