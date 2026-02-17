from typing import Optional

from pydantic import BaseModel
import datetime
import uuid


class UserTask(BaseModel):
    id: uuid.UUID
    text: str
    created_at: datetime.datetime
    is_complete: bool
    user_id: uuid.UUID

class UserTaskRequestAdd(BaseModel):
    text: str

class UserTaskRequestUpdate(BaseModel):
    user_task_id: uuid.UUID
    text: Optional[str] = None
    is_complete: Optional[bool] = None

class UserTaskRequestDelete(BaseModel):
    user_task_id: uuid.UUID

class UserTaskTextUpdate(BaseModel):
    text: str

class UserTaskCompleteUpdate(BaseModel):
    is_complete: bool

class UserTaskTextCompleteUpdate(BaseModel):
    text: str
    is_complete: bool

