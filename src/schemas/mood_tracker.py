from typing import Optional

from pydantic import BaseModel, Field
import datetime
import uuid


class MoodInfluenceFactorSelection(BaseModel):
    category_id: str
    option_ids: list[str] = Field(default_factory=list)
    custom_text: Optional[str] = None


class MoodInfluenceOption(BaseModel):
    id: str
    title: str


class MoodInfluenceCategory(BaseModel):
    id: str
    title: str
    allow_custom_text: bool = False
    options: list[MoodInfluenceOption] = Field(default_factory=list)


class MoodEmotionGroup(BaseModel):
    id: str
    title: str
    emotions: list[str] = Field(default_factory=list)


class MoodEmotionCatalog(BaseModel):
    groups: list[MoodEmotionGroup] = Field(default_factory=list)
    allow_custom_text: bool = True
    custom_title: str = "Другое"


class MoodTrackerDateRequestAdd(BaseModel):
    score: int
    day: Optional[datetime.date] = None
    emoji_ids: list[int] = Field(default_factory=list)
    emotions: list[str] = Field(default_factory=list)
    other_emotion: Optional[str] = None
    influence_factors: list[MoodInfluenceFactorSelection] = Field(default_factory=list)


class MoodTracker(BaseModel):
    id: uuid.UUID
    score: int
    created_at: datetime.datetime
    user_id: uuid.UUID
    emoji_ids: list[int] = Field(default_factory=list)
    emoji_texts: list[str] = Field(default_factory=list)
    emotions: list[str] = Field(default_factory=list)
    influence_factors: list[MoodInfluenceFactorSelection] = Field(default_factory=list)

class MoodTrackerCreate(BaseModel):
    id: uuid.UUID
    score: int
    created_at: datetime.datetime
    user_id: uuid.UUID
    emoji_ids: list[int] = Field(default_factory=list)
    emotions: list[str] = Field(default_factory=list)
    influence_factors: list[MoodInfluenceFactorSelection] = Field(default_factory=list)


class WeeklyMoodTrackerDay(BaseModel):
    date: datetime.date
    weekday: int
    mood_trackers: list[MoodTracker] = Field(default_factory=list)
