import uuid
import pydantic
from src.enums import DailyTaskType

class DailyTaskId(pydantic.BaseModel):
    daily_task_id: uuid.UUID

class DailyTaskResponse(pydantic.BaseModel):
    id: uuid.UUID
    title: str
    short_desc: str
    destination_id: uuid.UUID
    number: int
    day: int  # Добавлено поле day
    is_complete: bool
    is_current: bool
    type: DailyTaskType
    user_id: uuid.UUID

    class Config:
        use_enum_values = True

class DailyTaskUpdate(pydantic.BaseModel):
    is_complete: bool

class DailyTaskCreate(pydantic.BaseModel):
    title: str
    short_desc: str
    destination_id: uuid.UUID
    number: int
    day: int  # Добавлено поле day
    is_complete: bool
    is_current: bool
    type: DailyTaskType
    user_id: uuid.UUID

    class Config:
        use_enum_values = True