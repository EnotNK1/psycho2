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
    is_active: bool
    department: str
    #job_title: str
    face_to_face: bool


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
    is_active: Optional[bool] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    face_to_face: Optional[bool] = None


class GetAllManagerRequest(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    city: Optional[str] = None
    company: Optional[str] = None
    online: Optional[bool] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime.date] = None
    phone_number: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    face_to_face: Optional[bool] = None
    role_id: int


class ClientSchema(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    mentor_id: uuid.UUID
    text: str
    status: bool


class UserBase(BaseModel):
    email: EmailStr
    username: str
    role_id: int


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    birth_date: datetime.date
    gender: str
    city: Optional[str] = None
    phone_number: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    role_id: int

