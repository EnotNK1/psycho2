import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import DateTime


class UserRequestAdd(BaseModel):
    email: EmailStr
    username: str
    birth_date: datetime.date
    gender: str
    city: str
    phone_number: str
    password: str
    confirm_password: str


class UserRequestLogIn(BaseModel):
    email: EmailStr
    password: str


class UserAdd(BaseModel):
    email: EmailStr
    username: str
    birth_date: datetime.date
    gender: str
    city: str
    phone_number: str
    hashed_password: str
    role_id: int
    id: uuid.UUID


class User(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    birth_date: datetime.date
    gender: str
    city: str
    phone_number: Optional[str]


class UserWithHashedPassword(User):
    hashed_password: str
    role_id: int

class PasswordResetRequest(BaseModel):
    email: EmailStr


class HashedPassword(BaseModel):
    hashed_password: str


class PasswordChangeRequest(BaseModel):
    token: str
    password: str
    confirm_new_password: str

class BecomeManagerRequest(BaseModel):
    username: str
    description: str
    city: str
    company: str
    online: bool
    gender: str
    birth_date: str


class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    company: Optional[str] = None
    online: Optional[bool] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime.date] = None
    phone_number: Optional[str] = None

class UpdateManagerRequest(BaseModel):
    username: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    company: Optional[str] = None
    online: Optional[bool] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime.date] = None
    phone_number: Optional[str] = None
    role_id: Optional[int] = None

class GetAllManagerRequest(BaseModel):
    username: str
    description: Optional[str]
    city: Optional[str]
    company: Optional[str]
    online: Optional[bool]
    gender: Optional[str]
    birth_date: Optional[datetime.date]
    is_active: Optional[bool]
    department: Optional[str]
    phone_number: Optional[str]
    face_to_face: Optional[bool]