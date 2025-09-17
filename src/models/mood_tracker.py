from sqlalchemy import ARRAY, TEXT
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
import uuid
import datetime
import sqlalchemy as sa

class MoodTrackerOrm(Base):
    __tablename__ = "mood_tracker"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    score: Mapped[int]
    created_at: Mapped[datetime.datetime]
    user_id: Mapped[uuid.UUID]

    emoji_ids: Mapped[list[int]] = mapped_column(ARRAY(sa.Integer), nullable=True)