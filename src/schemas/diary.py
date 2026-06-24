from typing import Optional

from pydantic import BaseModel
import datetime
import uuid

from pydantic import ConfigDict


class DiaryDateRequestAdd(BaseModel):
    text: str
    day: str | None = None


class Diary(BaseModel):
    id: uuid.UUID
    text: str
    created_at: datetime.datetime
    user_id: uuid.UUID

class AbcDiary(BaseModel):
    id: uuid.UUID
    activating_event: str
    beliefs: str
    consequences: str
    user_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class AbcDiaryAdd(BaseModel):
    activating_event: str
    beliefs: str
    consequences: str

class AbcDiaryUpdate(BaseModel):
    activating_event: Optional[str] = None
    beliefs: Optional[str] = None
    consequences: Optional[str] = None