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
    hashed_password: Mapped[Optional[str]] = mapped_column(String(200))
    city: Mapped[Optional[str]]
    company: Mapped[Optional[str]]
    online: Mapped[Optional[bool]]
    gender: Mapped[str]
    birth_date: Mapped[Optional[datetime.date]]
    phone_number: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    role_id: Mapped[int]
    is_active: Mapped[Optional[bool]]
    department: Mapped[Optional[str]]
    job_title: Mapped[Optional[str]]
    face_to_face: Mapped[Optional[bool]]
    higher_education_university: Mapped[Optional[str]] = mapped_column(String(255))
    higher_education_specialization: Mapped[Optional[str]] = mapped_column(String(255))
    academic_degree: Mapped[Optional[str]] = mapped_column(String(100))
    courses: Mapped[Optional[str]] = mapped_column(String(400))
    work_format: Mapped[Optional[str]] = mapped_column(String(50))
    association: Mapped[Optional[str]] = mapped_column(String(200))
    avatar_link: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    inquiries: Mapped[list["InquiryOrm"]] = relationship(
        secondary=user_inquiry, back_populates="users"
    )

    @property
    def inquiry_texts(self) -> list[str]:
        return [inq.text for inq in self.inquiries]
