import datetime
from typing import Optional

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
    company: Mapped[Optional[str]]  # Поле может быть NULL
    online: Mapped[Optional[bool]]  # Поле может быть NULL
    gender: Mapped[str]
    birth_date: Mapped[Optional[datetime.date]]  # Поле может быть NULL
    phone_number: Mapped[Optional[str]]  # Поле может быть NULL
    description: Mapped[Optional[str]]  # Поле может быть NULL
    role_id: Mapped[int]
    is_active: Mapped[Optional[bool]]  # Поле может быть NULL
    department: Mapped[Optional[str]]  # Поле может быть NULL
    face_to_face: Mapped[Optional[bool]]  # Поле может быть NULL
