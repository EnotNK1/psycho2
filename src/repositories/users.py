from pydantic import EmailStr
from sqlalchemy import select

from src.models.users import UsersOrm
from src.repositories.mappers.mappers import UserDataMapper, AdminUserDataMapper
from src.schemas.users import UserWithHashedPassword
from src.repositories.base import BaseRepository


class UsersRepository(BaseRepository):
    model = UsersOrm
    mapper  = UserDataMapper
    admin_mapper = AdminUserDataMapper

    async def get_user_with_hashed_password(self, email: EmailStr):
        query = select(self.model).filter_by(email=email)
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return UserWithHashedPassword.model_validate(model, from_attributes=True)

    async def get_all_users_admin(self):
        query = select(self.model)
        result = await self.session.execute(query)
        return [self.admin_mapper.map_to_domain_entity(model) for model in result.scalars().all()]