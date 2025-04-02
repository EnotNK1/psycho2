import uuid
import datetime
from sqlalchemy import Boolean, Column, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base

class ApplicationOrm(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    manager_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(String(1000))
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    problem_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    problem: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)