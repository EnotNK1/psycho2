import uuid

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
    PasswordDoNotMatchException,
)
from src.schemas.users import UserRequestAdd, UserAdd, UserRequestLogIn, PasswordChangeRequest, HashedPassword

serializer = URLSafeTimedSerializer('secret_key')


class AuthService(BaseService):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode |= {"exp": expire}
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.exceptions.DecodeError:
            raise IncorrectTokenException

    async def register_user(self, data: UserRequestAdd):
        if data.password != data.confirm_password:
            raise PasswordDoNotMatchException
        hashed_password = self.hash_password(data.password)
        new_user_data = UserAdd(
            **data.model_dump(exclude={"password", "confirm_password"}),
            hashed_password=hashed_password,
            role_id=1,
            id=uuid.uuid4(),
        )
        try:
            await self.db.users.add(new_user_data)
            await self.db.commit()
        except ObjectAlreadyExistsException as ex:
            raise UserAlreadyExistsException from ex

    async def login_user(self, data: UserRequestLogIn) -> str:
        user = await self.db.users.get_user_with_hashed_password(email=data.email)
        if not user:
            raise EmailNotRegisteredException
        if not self.verify_password(data.password, user.hashed_password):
            raise IncorrectPasswordException
        access_token = self.create_access_token({"user_id": str(user.id)})
        return access_token

    async def get_one_or_none_user(self, **filter_by):
        return await self.db.users.get_one_or_none(**filter_by)

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