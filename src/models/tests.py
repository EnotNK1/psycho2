import datetime
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base
import uuid
from sqlalchemy import ForeignKey, Enum, JSON, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List


class TestOrm(Base):
    __tablename__ = "test"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    short_desc: Mapped[str]
    link: Mapped[str]

    test_result: Mapped[List["TestResultOrm"]] = relationship(cascade="all, delete-orphan")
    question: Mapped[List["QuestionOrm"]] = relationship(back_populates="test", cascade="all, delete-orphan")
    scale: Mapped[List["ScaleOrm"]] = relationship(cascade="all, delete-orphan")


class TestResultOrm(Base):
    __tablename__ = "test_result"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    test_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test.id", ondelete="CASCADE"))
    date: Mapped[datetime.datetime]

    scale_result: Mapped[List["ScaleResultOrm"]] = relationship(
        back_populates="test_result",
        cascade="all, delete-orphan",
        lazy="selectin"  # Используем selectin для асинхронной загрузки
    )

class ScaleOrm(Base):
    __tablename__ = "scale"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    min: Mapped[int]
    max: Mapped[int]
    test_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test.id", ondelete="CASCADE"), nullable=True)

    scale_result: Mapped[List["ScaleResultOrm"]] = relationship(cascade="all, delete-orphan")
    borders: Mapped[List["BordersOrm"]] = relationship(back_populates="scale", cascade="all, delete-orphan")


class ScaleResultOrm(Base):
    __tablename__ = "scale_result"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    score: Mapped[float]
    scale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scale.id", ondelete="CASCADE"))
    test_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_result.id", ondelete="CASCADE"))

    test_result: Mapped["TestResultOrm"] = relationship(back_populates="scale_result")


class BordersOrm(Base):
    __tablename__ = "borders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    left_border: Mapped[float]
    right_border: Mapped[float]
    color: Mapped[str]
    title: Mapped[str]
    user_recommendation: Mapped[str] = mapped_column(nullable=True)
    scale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scale.id", ondelete="CASCADE"))

    scale: Mapped["ScaleOrm"] = relationship(back_populates="borders")


class QuestionOrm(Base):
    __tablename__ = "question"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    text: Mapped[str]
    number: Mapped[int]
    test_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test.id", ondelete="CASCADE"))

    # Список ID ответов (хранится как JSON)
    answer_choice: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID), default=list)

    # Отношение к тесту
    test: Mapped["TestOrm"] = relationship(back_populates="question")

class AnswerChoiceOrm(Base):
    __tablename__ = "answer_choice"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    text: Mapped[str]
    score: Mapped[int]

