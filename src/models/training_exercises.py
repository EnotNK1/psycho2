import datetime

import uuid
from typing import List, Optional
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class TrainingExerciseOrm(Base):
    __tablename__ = 'training_exercise'

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str]
    description: Mapped[str]
    picture_link: Mapped[Optional[str]]
    time_to_read: Mapped[int]

    questions: Mapped[List["TrainingQuestionOrm"]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan"
    )
    completed: Mapped[List["TrainingCompletedExerciseOrm"]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan"
    )


class TrainingQuestionOrm(Base):
    __tablename__ = 'training_question'

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    text: Mapped[str]
    formulation: Mapped[str]

    training_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_exercise.id", ondelete="CASCADE")
    )

    exercise: Mapped["TrainingExerciseOrm"] = relationship(
        back_populates="questions"
    )
    variants: Mapped[List["TrainingVariantOrm"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan"
    )


class TrainingVariantOrm(Base):
    __tablename__ = 'training_variant'

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(nullable=False)
    correct: Mapped[bool]
    explanation: Mapped[str]

    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_question.id", ondelete="CASCADE")
    )

    question: Mapped["TrainingQuestionOrm"] = relationship(
        back_populates="variants"
    )


class TrainingCompletedExerciseOrm(Base):
    __tablename__ = 'completed_training_exercise'

    __table_args__ = (
        UniqueConstraint("training_exercise_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.utcnow
    )

    training_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_exercise.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"))

    exercise: Mapped["TrainingExerciseOrm"] = relationship(
        back_populates="completed"
    )
