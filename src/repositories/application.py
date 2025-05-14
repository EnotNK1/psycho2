from uuid import UUID
from sqlalchemy import select
from src.models.application import ApplicationOrm
from src.models.users import UsersOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import ApplicationDataMapper


class ApplicationRepository(BaseRepository):
    model = ApplicationOrm
    mapper = ApplicationDataMapper

    async def is_user_manager(self, user_id: UUID) -> bool:
        query = select(UsersOrm.role_id).where(UsersOrm.id == user_id)
        result = await self.session.execute(query)
        role_id = result.scalar_one_or_none()
        return role_id == 2
