from pydantic import BaseModel
import datetime
import uuid


class MoodTrackerDateRequestAdd(BaseModel):
    score: int
    day: str


class MoodTracker(BaseModel):
    id: uuid.UUID
    score: int
    created_at: datetime.datetime
    user_id: uuid.UUID