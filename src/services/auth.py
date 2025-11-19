import uuid

from typing import Tuple
from itsdangerous import URLSafeTimedSerializer, BadData
from passlib.context import CryptContext
from fastapi import HTTPException
import jwt
from datetime import datetime, timezone, timedelta

from sqlalchemy.testing.suite.test_reflection import users

from src.config import settings
from src.services.base import BaseService
from src.exceptions import (
    IncorrectTokenException,
    EmailNotRegisteredException,
    IncorrectPasswordException,
    ObjectAlreadyExistsException,
    UserAlreadyExistsException,
    PasswordDoNotMatchException, ObjectNotFoundException,
)
from src.schemas.users import (
    UserRequestAdd,
    UserAdd,
    UserRequestLogIn,
    PasswordChangeRequest,
    HashedPassword,
    UpdateUserRequest,
)
from src.services.daily_tasks import DailyTaskService

serializer = URLSafeTimedSerializer("secret_key")


class AuthService(BaseService):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_tokens(self, data: dict) -> Tuple[str, str]:
        to_encode = data.copy()

        # Access token
        access_token_expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode_access = to_encode.copy()
        to_encode_access.update({"exp": access_token_expire})
        access_token = jwt.encode(
            to_encode_access,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        # Refresh token
        refresh_token_expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode_refresh = to_encode.copy()
        to_encode_refresh.update({"exp": refresh_token_expire})
        refresh_token = jwt.encode(
            to_encode_refresh,
            settings.JWT_REFRESH_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        return access_token, refresh_token

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def decode_token(self, token: str, is_refresh: bool = False) -> dict:
        try:
            secret_key = settings.JWT_REFRESH_SECRET_KEY if is_refresh else settings.JWT_SECRET_KEY
            return jwt.decode(
                token,
                secret_key,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.exceptions.DecodeError:
            raise IncorrectTokenException
        except jwt.ExpiredSignatureError:
            raise IncorrectTokenException("Token expired")

    async def register_user(self, data: UserRequestAdd) -> Tuple[str, str]:
        if data.password != data.confirm_password:
            raise PasswordDoNotMatchException
        hashed_password = self.hash_password(data.password)
        new_user_data = UserAdd(
            **data.model_dump(exclude={"password", "confirm_password"}),
            hashed_password=hashed_password,
            role_id=1,
            id=uuid.uuid4()
        )

        try:
            await self.db.users.add(new_user_data)
            await self.db.commit()
            await DailyTaskService(self.db).add_daily_tasks_for_new_user(new_user_data.id)
        except ObjectAlreadyExistsException as ex:
            raise UserAlreadyExistsException from ex

        # токены для новых пользователей
        return self.create_tokens({"user_id": str(new_user_data.id), "role_id": new_user_data.role_id})

    async def login_user(self, data: UserRequestLogIn) -> Tuple[str, str]:
        user = await self.db.users.get_user_with_hashed_password(email=data.email)
        if not user:
            raise EmailNotRegisteredException
        if not self.verify_password(data.password, user.hashed_password):
            raise IncorrectPasswordException
        return self.create_tokens({"user_id": str(user.id), "role_id": user.role_id})

    async def refresh_tokens(self, refresh_token: str) -> Tuple[str, str]:
        try:
            payload = self.decode_token(refresh_token, is_refresh=True)
            user_id = payload.get("user_id")
            role_id = payload.get("role_id")

            user = await self.db.users.get_one_or_none(id=user_id)
            if not user:
                raise IncorrectTokenException("User not found")

            return self.create_tokens({"user_id": user_id, "role_id": role_id})
        except Exception as e:
            raise IncorrectTokenException(str(e))

    async def get_one_or_none_user(self, **filter_by):
        return await self.db.users.get_one_or_none(**filter_by)

    async def delete_user(self, **filter_by):
        return await self.db.users.delete(**filter_by)

    async def change_password(self, password_data: PasswordChangeRequest):
        try:
            email = serializer.loads(password_data.token, max_age=3600)
        except BadData:
            raise IncorrectTokenException
        if password_data.password != password_data.confirm_new_password:
            raise PasswordDoNotMatchException
        hashed_password = self.hash_password(password_data.password)
        _hashed_password = HashedPassword(hashed_password=hashed_password)
        await self.db.users.edit(_hashed_password, exclude_unset=True, email=email)
        await self.db.commit()

    async def update_user(self, user_id: uuid.UUID, data: UpdateUserRequest):
        user = await self.db.users.get_one_or_none(id=user_id)
        if not user:
            raise ObjectNotFoundException("User not found")

        # Обновляем данные пользователя
        await self.db.users.edit(data, exclude_unset=True, id=user_id)
        await self.db.commit()

    async def get_all_users_admin(self):
        return await self.db.users.get_all_users_admin()

    async def register_admin(self, email: str, password: str, username: str = "admin"):
        try:
            existing_user = await self.db.users.get_one_or_none(email=email)
            if existing_user:
                raise Exception("Пользователь с таким email уже существует")

            admin_data = {
                "email": email,
                "password": password,
                "username": username,
                "role_id": 0
            }

            user = await self.register_user(**admin_data)

            await self.db.commit()
            return user

        except Exception as e:
            await self.db.rollback()
            raise e
