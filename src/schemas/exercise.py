from __future__ import annotations
from datetime import date
from typing import List, Optional, Union
import uuid
from pydantic import BaseModel
from src import enums
# from models.exercise import FieldOrm, VariantOrm


class ExerciseBase(BaseModel):
    id: uuid.UUID
    title: str
    picture_link: str


class ExerciseViewCreate(BaseModel):
    view: str
    score: Optional[int] = None
    picture_link: str
    message: str


class ExerciseViewResponse(ExerciseViewCreate):
    open: bool = False

    class Config:
        from_attributes = True


class ExerciseCreate(BaseModel):
    title: str
    description: str
    picture_link: str
    time_to_read: int
    questions_count: int
    linked_exercise_id: Optional[uuid.UUID] = None  # Сделать опциональным

    class Config:
        from_attributes = True


class ExerciseResponse(ExerciseBase):
    open: bool = False

    class Config:
        from_attributes = True


class ExercisesListResponse(BaseModel):
    exercises: List[ExerciseResponse]


class ExerciseDetailResponse(ExerciseResponse):
    fields: List["FieldResponse"] = []

    class Config:
        from_attributes = True


class FieldBase(BaseModel):
    title: str
    major: bool
    view: enums.ViewType
    type: enums.FieldType
    placeholder: Optional[str] = None
    prompt: Optional[str] = None
    description: str
    order: int
    exercises: Optional[List[str]] = None


class FieldCreate(BaseModel):
    title: str
    major: bool
    view: enums.ViewType
    type: enums.FieldType
    placeholder: Optional[str] = None
    prompt: Optional[str] = None
    description: str
    order: int
    exercises: Optional[List[str]] = None


class FieldResponse(FieldBase):
    id: uuid.UUID
    exercise_structure_id: uuid.UUID
    variants: List[VariantResponse] = []

    # @classmethod
    # def from_orm(cls, field: FieldOrm):
    #     return cls(
    #         id=field.id,
    #         title=field.title,
    #         major=field.major,
    #         view=field.view,
    #         type=field.type,
    #         placeholder=field.placeholder,
    #         prompt=field.prompt,
    #         description=field.description,
    #         order=field.order,
    #         exercises=field.exercises,
    #         exercise_structure_id=field.exercise_structure_id,
    #         variants=[VariantResponse.from_orm(v) for v in field.variants]
    #     )


class VariantCreate(BaseModel):
    title: str


class VariantResponse(BaseModel):
    id: uuid.UUID
    title: str
    field_id: uuid.UUID

    # @classmethod
    # def from_orm(cls, variant: VariantOrm):
    #     return cls(
    #         id=variant.id,
    #         title=variant.title,
    #         field_id=variant.field_id
    #     )


class FilledFieldCreate(BaseModel):
    field_id: uuid.UUID
    text: Union[str, int, float, List[str], List[int], None]


class CompletedExerciseCreate(BaseModel):
    exercise_structure_id: uuid.UUID
    filled_fields: List[FilledFieldCreate]


class CompletedExerciseResponse(BaseModel):
    id: uuid.UUID
    score: int
    picture_link: Optional[str] = None
    view: Optional[str] = None
    success_message: Optional[str] = None

    class Config:
        from_attributes = True


class PulledFieldResponse(BaseModel):
    field_id: uuid.UUID
    title: str
    text: Union[str, int, float, List[str], List[int], None]
    source_exercise_id: uuid.UUID


class ExerciseDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    picture_link: str
    description: str
    time_to_read: int
    questions_count: int
    open: bool

    class Config:
        from_attributes = True


class SectionResponse(BaseModel):
    id: uuid.UUID
    title: str
    view: enums.ViewType
    type: enums.FieldType
    placeholder: Optional[str] = None
    prompt: Optional[str] = None
    variants: List[VariantResponse] = []


class PageResponse(BaseModel):
    page_number: int
    sections: List[SectionResponse] = []


class ExerciseDetail1Response(BaseModel):
    pulled_fields: List[PulledFieldResponse] = []
    id: uuid.UUID
    title: str
    picture_link: str
    description: str
    time_to_read: int
    questions_count: int
    open: bool
    pages: List[PageResponse] = []

    class Config:
        from_attributes = True
        populate_by_name = True


class ResultResponse(BaseModel):
    id: uuid.UUID
    exercise_id: uuid.UUID
    date: date
    preview: Union[str, int, float, List[str], List[int], None]

    class Config:
        from_attributes = True


class ResultSectionResponse(BaseModel):
    title: str
    view: enums.ViewType
    type: enums.FieldType
    value: Union[str, List[str]]  # может быть строкой или массивом строк


class ResultDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    picture_link: str
    description: str
    exercise_id: uuid.UUID
    date: date
    sections: List[ResultSectionResponse]

    class Config:
        from_attributes = True


class ExerciseResultsResponse(BaseModel):
    results: List[ResultResponse]


ExerciseDetailResponse.update_forward_refs()
FieldResponse.update_forward_refs()
