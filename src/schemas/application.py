import uuid
from datetime import date
from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    user_id: uuid.UUID
    text: str


class ApplicationShortResponse(BaseModel):
    app_id: uuid.UUID
    client_id: uuid.UUID
    username: str
    text: str
    online: bool
    problem_id: uuid.UUID | None
    problem: str | None


class ApplicationFullResponse(BaseModel):
    app_id: uuid.UUID
    client_id: uuid.UUID
    is_active: bool
    username: str
    birth_date: date | None
    gender: str | None
    text: str


class ApplicationStatusUpdate(BaseModel):
    user_id: uuid.UUID
    status: bool