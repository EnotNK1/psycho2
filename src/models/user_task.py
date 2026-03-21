from sqlalchemy import ARRAY, TEXT
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
import uuid
import datetime
import sqlalchemy as sa

class UserTaskOrm(Base):
    __tablename__ = "user_task"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    text: Mapped[str]
    created_at: Mapped[datetime.datetime]
    completed_at: Mapped[datetime.datetime] = mapped_column(nullable=True)
    is_complete: Mapped[bool]
    user_id: Mapped[uuid.UUID]
