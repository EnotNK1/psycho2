import datetime
import uuid
from typing import Any, List

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.enums import FieldType, ViewType
from src.utils.encryption import EncryptedJSONType


class ExerciseStructureOrm(Base):
    __tablename__ = "exercise_structure"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    picture_link: Mapped[str]
    time_to_read: Mapped[int]
    questions_count: Mapped[int]
    sort_order: Mapped[int]
    group: Mapped[int]
    linked_exercise_id: Mapped[uuid.UUID] = mapped_column(nullable=True)
    completed_exercise: Mapped[List["CompletedExerciseOrm"]] = relationship(
        cascade="all, delete-orphan"
    )
    field: Mapped[List["FieldOrm"]] = relationship(
        cascade="all, delete-orphan")


class CompletedExerciseOrm(Base):
    __tablename__ = "completed_exercise"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    date: Mapped[datetime.datetime]
    exercise_structure_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercise_structure.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    filled_field: Mapped[List["FilledFieldOrm"]] = relationship(
        cascade="all, delete-orphan"
    )


class FieldOrm(Base):
    __tablename__ = "field"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    major: Mapped[bool]
    view: Mapped[ViewType] = mapped_column(String(20))
    type: Mapped[FieldType] = mapped_column(String(20))
    placeholder: Mapped[str] = mapped_column(nullable=True)
    prompt: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str]
    order: Mapped[int]
    position: Mapped[int]
    pull_group: Mapped[str] = mapped_column(nullable=True)
    exercise_structure_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercise_structure.id", ondelete="CASCADE")
    )
    variants: Mapped[List["VariantOrm"]] = relationship(
        cascade="all, delete-orphan", back_populates="field"
    )
    exercises: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(String), nullable=True)
    filled_field: Mapped[List["FilledFieldOrm"]] = relationship(
        cascade="all, delete-orphan"
    )


class VariantOrm(Base):
    __tablename__ = "variants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("field.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(nullable=False)
    field: Mapped["FieldOrm"] = relationship(back_populates="variants")


class FilledFieldOrm(Base):
    __tablename__ = "filled_field"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=True)
    view: Mapped[ViewType] = mapped_column(String(20))
    type: Mapped[FieldType] = mapped_column(String(20))
    text: Mapped[Any] = mapped_column(EncryptedJSONType())
    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("field.id", ondelete="CASCADE")
    )
    completed_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("completed_exercise.id", ondelete="CASCADE")
    )
    exercises: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)
    source_group_key: Mapped[str] = mapped_column(nullable=True)
    pulled_completed_exercise_id: Mapped[uuid.UUID] = mapped_column(nullable=True)
    pulled_group_key: Mapped[str] = mapped_column(nullable=True)
    pulled_fields_snapshot: Mapped[Any] = mapped_column(
        EncryptedJSONType(), nullable=True
    )


class ExerciseViewOrm(Base):
    __tablename__ = "exercise_view"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    exercise_structure_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercise_structure.id", ondelete="CASCADE")
    )
    view: Mapped[str] = mapped_column(nullable=True)
    score: Mapped[int] = mapped_column(nullable=True)
    picture_link: Mapped[str] = mapped_column(nullable=True)
    message: Mapped[str] = mapped_column(nullable=True)
