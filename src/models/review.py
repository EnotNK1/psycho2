from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
import uuid
import datetime


class ReviewOrm(Base):
    __tablename__ = "review"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    text: Mapped[str]
    email: Mapped[str]
    is_read: Mapped[bool]
    created_at: Mapped[datetime.datetime]
