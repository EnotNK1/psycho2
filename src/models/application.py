import uuid
import datetime
from typing import List
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER
from sqlalchemy import Boolean, Column, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base

class ApplicationOrm(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    manager_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    inquiry: Mapped[List[int]] = mapped_column(ARRAY(INTEGER), default=list)
    text: Mapped[str] = mapped_column(String(1000))
    status: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)