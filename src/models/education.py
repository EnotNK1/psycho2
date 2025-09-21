import uuid
from typing import List, Optional, Any

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.users import UsersOrm


class educationThemeOrm(Base):
    def __init__(self, **kw: Any):
        super().__init__(kw)
        self.awaitable_attrs = None

    __tablename__ = "education_theme"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    theme: Mapped[str]
    link: Mapped[str]
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    related_topics: Mapped[Optional[List[str]]
                           ] = mapped_column(JSON, nullable=True)

    education_materials: Mapped[List["educationMaterialOrm"]] = relationship(
        back_populates="education_theme",
        cascade="all, delete-orphan"
    )


class educationMaterialOrm(Base):
    def __init__(self, **kw: Any):
        super().__init__(kw)
        self.awaitable_attrs = None

    __tablename__ = "education_material"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    type: Mapped[int]
    number: Mapped[int]
    title: Mapped[Optional[str]]
    link_to_picture: Mapped[Optional[str]]
    education_theme_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("education_theme.id", ondelete="CASCADE")
    )
    subtitle: Mapped[Optional[str]]

    education_theme: Mapped["educationThemeOrm"] = relationship(
        back_populates="education_materials"
    )
    education_progresses: Mapped[List["EducationProgressOrm"]] = relationship(
        back_populates="education_material",
        cascade="all, delete-orphan"
    )
    cards: Mapped[List["CardOrm"]] = relationship(
        back_populates="education_material",
        cascade="all, delete-orphan"
    )


class CardOrm(Base):
    __tablename__ = "education_card"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    text: Mapped[str]
    number: Mapped[int]
    link_to_picture: Mapped[Optional[str]]

    education_material_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("education_material.id", ondelete="CASCADE")
    )

    education_material: Mapped["educationMaterialOrm"] = relationship(
        back_populates="cards"
    )


class EducationProgressOrm(Base):
    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self.awaitable_attrs = None

    __tablename__ = "education_progress"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True,
                                          default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    education_material_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("education_material.id", ondelete="CASCADE")
    )

    user: Mapped["UsersOrm"] = relationship(
        back_populates="education_progress")
    education_material: Mapped["educationMaterialOrm"] = relationship(
        back_populates="education_progresses"
    )
