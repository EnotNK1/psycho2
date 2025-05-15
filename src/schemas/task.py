import uuid
from typing import Optional

from pydantic import BaseModel


class TaskRequest(BaseModel):
    text: str
    test_id: uuid.UUID
    client_ids: Optional[list[uuid.UUID]] = None  # Список клиентов (опционально)

class TaskId(BaseModel):
    task_id: uuid.UUID


class Task(BaseModel):
    id: uuid.UUID
    text: str
    test_title: str
    test_id: uuid.UUID
    mentor_id: uuid.UUID
    client_id: uuid.UUID
    is_complete: bool
