import uuid
import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr


class ClientAdd(BaseModel):
    email: EmailStr
    username: str
    birth_date: datetime.date
    gender: str
    city: str
    phone_number: str
    hashed_password: str
    role_id: int
    id: uuid.UUID


class Client(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    birth_date: datetime.date
    gender: str
    city: str
    phone_number: Optional[str]


class ClientSchema(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    mentor_id: uuid.UUID
    text: str
    status: bool

class ClientGet(BaseModel):
    id: uuid.UUID
    username: str
    birth_date: datetime.date
    text: str
    gender: str
    inquiry: List[int]