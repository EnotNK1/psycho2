import uuid
from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
from src.enums import DailyTaskType

class DailyTaskOrm(Base):
    __tablename__ = "daily_task"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4  # Добавьте это
    )
    title: Mapped[str]
    short_desc: Mapped[str]
    destination_id: Mapped[uuid.UUID]
    number: Mapped[int]
    day: Mapped[int]
    is_complete: Mapped[bool]
    is_current: Mapped[bool]
    type: Mapped[DailyTaskType] = mapped_column(Enum(DailyTaskType))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))