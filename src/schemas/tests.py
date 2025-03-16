import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class ScaleResult(BaseModel):
    id: uuid.UUID
    score: float
    scale_id: uuid.UUID
    test_result_id: uuid.UUID


class TestResultRequest(BaseModel):
    test_id: uuid.UUID
    date: datetime.datetime
    results: list[float]


class TestResult(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    test_id: uuid.UUID
    date: datetime.datetime
    scale_result: list[ScaleResult]


class BordersAdd(BaseModel):
    id: uuid.UUID
    left_border: float
    right_border: float
    color: str
    title: str
    user_recommendation: str
    scale_id: uuid.UUID


class Borders(BaseModel):
    id: uuid.UUID
    left_border: float
    right_border: float
    color: str
    title: str
    user_recommendation: str
    scale_id: uuid.UUID


class AnswerChoice(BaseModel):
    id: uuid.UUID
    text: str
    score: int


class Question(BaseModel):
    id: uuid.UUID
    text: str
    number: int
    test_id: uuid.UUID
    answer_choice: list[uuid.UUID]


class ScaleAdd(BaseModel):
    id: uuid.UUID
    title: str
    min: int
    max: int
    test_id: Optional[uuid.UUID] = Field(default=None)  # Поле может быть None


class Scale(ScaleAdd):
    scale_result: list[ScaleResult] = []  # Поле по умолчанию пустое
    borders: list[Borders] = []  # Поле по умолчанию пустое


class TestAdd(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    short_desc: str
    link: str


class Test(TestAdd):
    test_result: list[TestResult]
    question: list[Question]
    scale: list[Scale]


class BorderDetail(BaseModel):
    id: uuid.UUID
    left_border: float
    right_border: float
    color: str
    title: str
    user_recommendation: str


class ScaleDetail(BaseModel):
    id: uuid.UUID
    title: str
    min: int
    max: int
    borders: list[BorderDetail]


class AnswerChoiceDetail(BaseModel):
    id: uuid.UUID
    text: str
    score: int


class QuestionDetail(BaseModel):
    id: uuid.UUID
    text: str
    number: int
    answers: list[AnswerChoiceDetail]


class TestDetailsResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    short_desc: str
    link: str
    scales: list[ScaleDetail]
    questions: list[QuestionDetail]
