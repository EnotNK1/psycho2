import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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


class TestSaveResult(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    test_id: uuid.UUID
    date: datetime.datetime


class BordersAdd(BaseModel):
    id: uuid.UUID
    left_border: float
    right_border: float
    color: str
    title: str
    user_recommendation: str
    scale_id: uuid.UUID


class BorderCreate(BaseModel):
    left_border: float
    right_border: float
    color: str
    title: str
    user_recommendation: str


class BordersUpdate(BaseModel):
    left_border: Optional[float] = None
    right_border: Optional[float] = None
    color: Optional[str] = None
    title: Optional[str] = None
    user_recommendation: Optional[str] = None
    scale_id: Optional[uuid.UUID] = None


class Borders(BaseModel):
    id: uuid.UUID
    left_border: float
    right_border: float
    color: str
    title: str
    user_recommendation: str
    scale_id: uuid.UUID


class BorderResponse(BordersAdd):
    model_config = ConfigDict(from_attributes=True)


class AnswerChoice(BaseModel):
    id: uuid.UUID
    text: str
    score: int


class AnswerChoiceCreate(BaseModel):
    text: str
    score: int


class AnswerChoiceUpdate(BaseModel):
    text: Optional[str] = None
    score: Optional[int] = None


class AnswerChoiceResponse(BaseModel):
    id: uuid.UUID
    text: str
    score: int

    model_config = ConfigDict(from_attributes=True)


class Question(BaseModel):
    id: uuid.UUID
    text: str
    opposite_text: Optional[str] = None
    number: int
    test_id: uuid.UUID
    answer_choice: list[uuid.UUID]


class QuestionCreate(BaseModel):
    text: str
    opposite_text: Optional[str] = None
    number: int
    answer_choice: list[uuid.UUID] = Field(default_factory=list)


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    opposite_text: Optional[str] = None
    number: Optional[int] = None
    test_id: Optional[uuid.UUID] = None
    answer_choice: Optional[list[uuid.UUID]] = None


class QuestionResponse(Question):
    model_config = ConfigDict(from_attributes=True)


class ScaleAdd(BaseModel):
    id: uuid.UUID
    title: str
    min: int
    max: int
    test_id: Optional[uuid.UUID] = Field(default=None)


class ScaleCreate(BaseModel):
    title: str
    min: int
    max: int


class ScaleUpdate(BaseModel):
    title: Optional[str] = None
    min: Optional[int] = None
    max: Optional[int] = None
    test_id: Optional[uuid.UUID] = None


class Scale(ScaleAdd):
    scale_result: list[ScaleResult] = Field(default_factory=list)
    borders: list[Borders] = Field(default_factory=list)


class ScaleResponse(ScaleAdd):
    model_config = ConfigDict(from_attributes=True)


class TestAdd(BaseModel):
    id: uuid.UUID
    title: str
    type: Optional[int] = None
    description: str
    short_desc: str
    link: str


class TestCreate(BaseModel):
    title: str
    type: Optional[int] = None
    description: str
    short_desc: str
    link: str


class TestUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[int] = None
    description: Optional[str] = None
    short_desc: Optional[str] = None
    link: Optional[str] = None


class Test(TestAdd):
    test_result: list[TestResult]
    question: list[Question]
    scale: list[Scale]


class TestResponse(TestAdd):
    model_config = ConfigDict(from_attributes=True)


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
    opposite_text: Optional[str] = None
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
