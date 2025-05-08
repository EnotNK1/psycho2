import datetime

import uuid
from typing import List
from sqlalchemy import ForeignKey, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

from src.schemas.exercise import FieldType
from src.database import Base


class ExerciseStructureOrm(Base):
    __tablename__ = 'exercise_structure'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    picture_link: Mapped[str]
    linked_exercise_id: Mapped[uuid.UUID] = mapped_column(nullable=True)
    field_count: Mapped[int]
    completed_exercise: Mapped[List["CompletedExerciseOrm"]] = relationship(
        cascade="all, delete-orphan")
    field: Mapped[List["FieldOrm"]] = relationship(
        cascade="all, delete-orphan")


class CompletedExerciseOrm(Base):
    __tablename__ = 'completed_exercise'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    date: Mapped[datetime.datetime]
    exercise_structure_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exercise_structure.id",
                                                                        ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"))
    filled_field: Mapped[List["FilledFieldOrm"]] = relationship(
        cascade="all, delete-orphan")


class FieldOrm(Base):
    __tablename__ = 'field'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    hint: Mapped[str]
    description: Mapped[str]
    type: Mapped[FieldType] = mapped_column(Enum(
        FieldType, name="fieldtype", create_constraint=True, values_callable=lambda x: [e.value for e in FieldType]))
    major: Mapped[bool]
    exercise_structure_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exercise_structure.id",
                                                                        ondelete="CASCADE"))
    order: Mapped[int]
    variants: Mapped[List["VariantOrm"]] = relationship(
        cascade="all, delete-orphan", back_populates="field"
    )
    exercises: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(String), nullable=True)
    filled_field: Mapped[List["FilledFieldOrm"]] = relationship(
        cascade="all, delete-orphan")


class VariantOrm(Base):
    __tablename__ = 'variants'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("field.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    field: Mapped["FieldOrm"] = relationship(back_populates="variants")


class FilledFieldOrm(Base):
    __tablename__ = 'filled_field'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    text: Mapped[str]
    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("field.id", ondelete="CASCADE"))
    completed_exercise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("completed_exercise.id",
                                                                        ondelete="CASCADE"))
    exercises: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)
