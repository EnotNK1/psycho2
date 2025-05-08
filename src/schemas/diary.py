from pydantic import BaseModel
import datetime
import uuid

class DiaryDateRequestAdd(BaseModel):
    text: str
    day: str | None = None


class Diary(BaseModel):
    id: uuid.UUID
    text: str
    created_at: datetime.datetime
    user_id: uuid.UUID
