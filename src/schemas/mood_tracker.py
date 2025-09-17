from typing import Optional

from pydantic import BaseModel
import datetime
import uuid


class MoodTrackerDateRequestAdd(BaseModel):
    score: int
    day: Optional[datetime.date] = None
    emoji_ids: list[int] = []


class MoodTracker(BaseModel):
    id: uuid.UUID
    score: int
    created_at: datetime.datetime
    user_id: uuid.UUID
    emoji_ids: list[int] = []
    emoji_texts: list[str] = []

class MoodTrackerCreate(BaseModel):
    id: uuid.UUID
    score: int
    created_at: datetime.datetime
    user_id: uuid.UUID
    emoji_ids: list[int] = []
