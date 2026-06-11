from typing import Optional

from pydantic import BaseModel, Field
import datetime
import uuid


class MoodTrackerDateRequestAdd(BaseModel):
    score: int
    day: Optional[datetime.date] = None
    emoji_ids: list[int] = Field(default_factory=list)


class MoodTracker(BaseModel):
    id: uuid.UUID
    score: int
    created_at: datetime.datetime
    user_id: uuid.UUID
    emoji_ids: list[int] = Field(default_factory=list)
    emoji_texts: list[str] = Field(default_factory=list)

class MoodTrackerCreate(BaseModel):
    id: uuid.UUID
    score: int
    created_at: datetime.datetime
    user_id: uuid.UUID
    emoji_ids: list[int] = Field(default_factory=list)


class WeeklyMoodTrackerDay(BaseModel):
    date: datetime.date
    weekday: int
    mood_trackers: list[MoodTracker] = Field(default_factory=list)
