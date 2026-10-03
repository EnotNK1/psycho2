from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
from src.database import Base
import uuid
import datetime
from src.utils.encryption import EncryptedStringType


class DiaryOrm(Base):
    __tablename__ = "diary"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(EncryptedStringType())
    created_at: Mapped[datetime.datetime]
    user_id: Mapped[uuid.UUID]
    mood_tracker_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("mood_tracker.id", ondelete="SET NULL"),
        nullable=True,
    )

class AbcDiaryEntryOrm(Base):
    __tablename__ = "abc_diary_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID]
    activating_event: Mapped[str]
    beliefs: Mapped[str]
    consequences: Mapped[str]
    created_at: Mapped[datetime.datetime]
    updated_at: Mapped[datetime.datetime]
