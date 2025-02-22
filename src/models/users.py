import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from src.database import Base
import uuid


class UsersOrm(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str] = mapped_column(String(200), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(200))
    city: Mapped[str]
    company: Mapped[str | None]
    online: Mapped[bool | None]
    face_to_face: Mapped[bool | None]
    gender: Mapped[str]
    birth_date: Mapped[datetime.date | None]
    phone_number: Mapped[str | None]
    description: Mapped[str | None]
    role_id: Mapped[int]
    is_active: Mapped[bool | None]
    department: Mapped[str | None]
