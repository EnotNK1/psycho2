from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
import uuid
import datetime


class DiaryOrm(Base):
    __tablename__ = "diary"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    text: Mapped[str]
    created_at: Mapped[datetime.datetime]
    user_id: Mapped[uuid.UUID]