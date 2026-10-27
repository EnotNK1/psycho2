import uuid
import datetime
from typing import List
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER
from sqlalchemy import Boolean, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class ApplicationOrm(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("client_id", "manager_id", name="uq_applications_pair"),
        Index("ix_applications_lookup", "manager_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    manager_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    inquiry: Mapped[List[int]] = mapped_column(ARRAY(INTEGER), default=list)
    text: Mapped[str] = mapped_column(String(1000))
    status: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
