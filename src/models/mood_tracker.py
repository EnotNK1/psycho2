from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
import uuid
import datetime


class MoodTrackerOrm(Base):
    __tablename__ = "mood_tracker"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    score: Mapped[int]
    created_at: Mapped[datetime.datetime]