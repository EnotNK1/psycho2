from sqlalchemy import ARRAY, TEXT
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
import uuid
import datetime
import sqlalchemy as sa
from src.utils.encryption import EncryptedIntType

class MoodTrackerOrm(Base):
    __tablename__ = "mood_tracker"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    score: Mapped[int] = mapped_column(EncryptedIntType())
    created_at: Mapped[datetime.datetime]
    user_id: Mapped[uuid.UUID]

    emoji_ids: Mapped[list[int]] = mapped_column(ARRAY(sa.Integer), nullable=True)
