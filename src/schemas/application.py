import uuid
from datetime import date
import datetime
from typing import List
from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    manager_id: uuid.UUID
    text: str
    inquiry: List[int]


class Application(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    manager_id: uuid.UUID
    status: bool
    text: str
    inquiry: List[int]
    created_at: datetime.datetime


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    manager_id: uuid.UUID
    status: bool
    text: str
    inquiry: List[int]
    created_at: datetime.datetime


class ApplicationStatusUpdate(BaseModel):
    app_id: uuid.UUID
    status: bool