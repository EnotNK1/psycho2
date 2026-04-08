import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from src.database import Base
import uuid

from src.models.user_inquiry import user_inquiry
from src.models.inquiry import InquiryOrm


class UsersOrm(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str] = mapped_column(String(200), unique=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(200))  # Поле может быть NULL
    city: Mapped[Optional[str]]  # Поле может быть NULL
    company: Mapped[Optional[str]]  # Поле может быть NULL
    online: Mapped[Optional[bool]]  # Поле может быть NULL
    gender: Mapped[str]
    birth_date: Mapped[Optional[datetime.date]]  # Поле может быть NULL
    phone_number: Mapped[Optional[str]]  # Поле может быть NULL
    description: Mapped[Optional[str]]  # Поле может быть NULL
    role_id: Mapped[int]
    is_active: Mapped[Optional[bool]]  # Поле может быть NULL
    department: Mapped[Optional[str]]  # Поле может быть NULL
    job_title: Mapped[Optional[str]]  # Поле может быть NULL
    face_to_face: Mapped[Optional[bool]]  # Поле может быть NULL

    higher_education_university: Mapped[Optional[str]] = mapped_column(String(255))
    higher_education_specialization: Mapped[Optional[str]] = mapped_column(String(255))
    academic_degree: Mapped[Optional[str]] = mapped_column(String(100))
    courses: Mapped[Optional[str]] = mapped_column(String(400))
    work_format: Mapped[Optional[str]] = mapped_column(String(50))
    association: Mapped[Optional[str]] = mapped_column(String(200))

    inquiries: Mapped[list["InquiryOrm"]] = relationship(
        secondary=user_inquiry, back_populates="users"
    )

    @property
    def inquiry_texts(self) -> list[str]:
        return [inq.text for inq in self.inquiries]

    education_progress = relationship(
        "EducationProgressOrm", back_populates="user", cascade="all, delete-orphan")


