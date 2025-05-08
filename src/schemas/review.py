import uuid
import datetime

from pydantic import BaseModel, EmailStr


class ReviewRequestAdd(BaseModel):
    text: str


class Review(ReviewRequestAdd):
    id: uuid.UUID
    email: str
    is_read: bool
    created_at: datetime.datetime


class ReviewRead(BaseModel):
    is_read: bool
