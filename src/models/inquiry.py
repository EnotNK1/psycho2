from typing import List

from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.database import Base


from sqlalchemy.orm import relationship

from src.models.user_inquiry import user_inquiry


class InquiryOrm(Base):
    __tablename__ = "inquiry"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str]

    users: Mapped[list["UsersOrm"]] = relationship(
        secondary=user_inquiry, back_populates="inquiries"
    )


