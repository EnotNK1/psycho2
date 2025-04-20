from typing import List

from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.database import Base


class InquiryOrm(Base):
    __tablename__ = "inquiry"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str]


