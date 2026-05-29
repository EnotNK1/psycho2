from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional, Union
import uuid

from pydantic import BaseModel, Field

from src import enums


class ExerciseBase(BaseModel):
    id: uuid.UUID
    title: str
    picture_link: str
    sort_order: int
    group: int


class ExerciseViewCreate(BaseModel):
    view: str
    score: Optional[int] = None
    picture_link: str
    message: str


class ExerciseViewUpdate(BaseModel):
    view: Optional[str] = None
    score: Optional[int] = None
    picture_link: Optional[str] = None
    message: Optional[str] = None


class ExerciseViewResponse(ExerciseViewCreate):
    id: uuid.UUID
    open: bool = False

    class Config:
        from_attributes = True


class ExerciseCreate(BaseModel):
    title: str
    description: str
    picture_link: str
    time_to_read: int
    questions_count: int
    sort_order: int
    group: int = 1
    linked_exercise_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class ExerciseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    picture_link: Optional[str] = None
    time_to_read: Optional[int] = None
    questions_count: Optional[int] = None
    sort_order: Optional[int] = None
    group: Optional[int] = None
    linked_exercise_id: Optional[uuid.UUID] = None


class ExerciseAutoCreate(ExerciseCreate):
    id: uuid.UUID


class ExerciseResponse(ExerciseBase):
    open: bool = False

    class Config:
        from_attributes = True


class ExercisesListResponse(BaseModel):
    regular_exercises: List[ExerciseResponse] = Field(default_factory=list)
    related_exercises: List[ExerciseResponse] = Field(default_factory=list)


class CompletedExerciseItemResponse(BaseModel):
    id: uuid.UUID
    title: str
    picture_link: str
    date: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompletedExercisesListResponse(BaseModel):
    exercises: List[CompletedExerciseItemResponse]


class FieldBase(BaseModel):
    title: str
    major: bool
    view: enums.ViewType
    type: enums.FieldType
    placeholder: Optional[str] = None
    prompt: Optional[str] = None
    description: str
    order: int
    position: int
    pull_group: Optional[str] = None
    exercises: Optional[List[uuid.UUID]] = None


class FieldCreate(BaseModel):
    title: str
    major: bool
    view: enums.ViewType
    type: enums.FieldType
    placeholder: Optional[str] = None
    prompt: Optional[str] = None
    description: str
    order: int
    position: int
    pull_group: Optional[str] = None
    exercises: Optional[List[uuid.UUID]] = None


class FieldUpdate(BaseModel):
    title: Optional[str] = None
    major: Optional[bool] = None
    view: Optional[enums.ViewType] = None
    type: Optional[enums.FieldType] = None
    placeholder: Optional[str] = None
    prompt: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    position: Optional[int] = None
    pull_group: Optional[str] = None
    exercises: Optional[List[uuid.UUID]] = None


class FieldAutoCreate(FieldCreate):
    id: uuid.UUID
    exercise_structure_id: uuid.UUID

    model_config = {
        "populate_by_name": True,
        "use_enum_values": True,
    }


class VariantCreate(BaseModel):
    title: str


class VariantUpdate(BaseModel):
    title: Optional[str] = None


class VariantResponse(BaseModel):
    id: uuid.UUID
    title: str
    field_id: uuid.UUID

    class Config:
        from_attributes = True


class FieldResponse(FieldBase):
    id: uuid.UUID
    exercise_structure_id: uuid.UUID
    variants: List[VariantResponse] = Field(default_factory=list)


class FilledFieldCreate(BaseModel):
    field_id: uuid.UUID
    text: Union[str, int, float, List[str], List[int]]
    pulled_completed_exercise_id: Optional[uuid.UUID] = None
    pulled_group_key: Optional[str] = None


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


class PulledFieldItemResponse(BaseModel):
    source_filled_field_id: uuid.UUID
    field_id: uuid.UUID
    title: str
    text: Union[str, int, float, List[str], List[int], None]
    source_group_key: str


class PulledFieldResponse(BaseModel):
    source_completed_exercise_id: uuid.UUID
    source_exercise_id: uuid.UUID
    source_group_key: str
    fields: List[PulledFieldItemResponse] = Field(default_factory=list)


class ExerciseDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    picture_link: str
    description: str
    time_to_read: int
    questions_count: int
    sort_order: int
    group: int
    open: bool

    class Config:
        from_attributes = True


class SectionResponse(BaseModel):
    id: uuid.UUID
    title: str
    view: enums.ViewType
    type: enums.FieldType
    position: int
    placeholder: Optional[str] = None
    prompt: Optional[str] = None
    variants: List[VariantResponse] = Field(default_factory=list)


class PageResponse(BaseModel):
    page_number: int
    sections: List[SectionResponse] = Field(default_factory=list)


class ExerciseDetail1Response(BaseModel):
    pulled_fields: List[PulledFieldResponse] = Field(default_factory=list)
    id: uuid.UUID
    title: str
    picture_link: str
    description: str
    time_to_read: int
    questions_count: int
    sort_order: int
    group: int
    open: bool
    pages: List[PageResponse] = Field(default_factory=list)

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
    value: Union[str, int, float, List[str], List[int], None]
    pulled_completed_exercise_id: Optional[uuid.UUID] = None
    pulled_group_key: Optional[str] = None
    pulled_fields: List[PulledFieldItemResponse] = Field(default_factory=list)


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


FieldResponse.model_rebuild()
