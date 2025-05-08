from __future__ import annotations
from enum import Enum
from typing import List, Optional
import uuid
from pydantic import BaseModel


class FieldType(Enum):
    TEXT = "TEXT"
    SLIDER = "SLIDER"
    CHOICE = "CHOICE"
    SELECTION = "SELECTION"


class ExerciseBase(BaseModel):
    title: str
    description: str
    picture_link: str
    linked_exercise_id: Optional[uuid.UUID] = None


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseResponse(ExerciseBase):
    id: uuid.UUID
    field_count: int
    open: bool = False

    class Config:
        from_attributes = True


class ExerciseDetailResponse(ExerciseResponse):
    fields: List["FieldResponse"] = []

    class Config:
        from_attributes = True


class FieldBase(BaseModel):
    title: str
    hint: str
    description: str
    type: FieldType
    major: bool
    order: int
    exercises: Optional[List[str]] = None


class FieldCreate(BaseModel):
    title: str
    hint: str
    description: str
    type: FieldType
    major: bool
    order: int
    exercises: Optional[List[str]] = None


class FieldResponse(FieldBase):
    id: uuid.UUID
    exercise_structure_id: uuid.UUID
    variants: List[VariantResponse] = []

    @classmethod
    def from_orm(cls, field: FieldOrm):
        return cls(
            id=field.id,
            title=field.title,
            hint=field.hint,
            description=field.description,
            type=field.type,
            major=field.major,
            order=field.order,
            exercises=field.exercises,
            exercise_structure_id=field.exercise_structure_id,
            variants=[VariantResponse.from_orm(v) for v in field.variants]
        )


class VariantBase(BaseModel):
    title: str


class VariantCreate(VariantBase):
    pass


class VariantResponse(VariantBase):
    id: uuid.UUID
    field_id: uuid.UUID

    @classmethod
    def from_orm(cls, variant: VariantOrm):
        return cls(
            id=variant.id,
            title=variant.title,
            field_id=variant.field_id
        )


class FilledFieldCreate(BaseModel):
    field_id: uuid.UUID
    text: str
    exercises: Optional[List[str]] = None


class CompletedExerciseCreate(BaseModel):
    exercise_structure_id: uuid.UUID
    filled_fields: List[FilledFieldCreate]


class PulledFieldResponse(BaseModel):
    field_id: uuid.UUID
    text: str
    source_exercise_id: uuid.UUID


class ExerciseDetailResponse(ExerciseResponse):
    pulled_fields: List[PulledFieldResponse] = []
    fields: List["FieldResponse"] = []

    class Config:
        from_attributes = True


ExerciseDetailResponse.update_forward_refs()
FieldResponse.update_forward_refs()
