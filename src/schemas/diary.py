from pydantic import BaseModel
import datetime
import uuid


class DiaryRequestAdd(BaseModel):
    text: str

class DiaryDateRequestAdd(BaseModel):
    text: str
    day: str

class Diary(BaseModel):
    id: uuid.UUID
    text: str
    created_at: datetime.datetime


class DiaryCheckResponse(BaseModel):
    date: int
    diary: bool







