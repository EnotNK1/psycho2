from typing import List, Optional

import uuid

from pydantic import Field, BaseModel


class CardResponse(BaseModel):
    id: uuid.UUID
    text: str
    number: int
    link_to_picture: Optional[str] = None


class EducationMaterialResponse(BaseModel):
    id: uuid.UUID
    type: int
    number: int
    title: Optional[str] = None
    link_to_picture: Optional[str] = None
    subtitle: Optional[str] = None
    cards: List[CardResponse] = Field(default_factory=list)


class ThemeRecommendationResponse(BaseModel):
    id: uuid.UUID
    theme: str
    link: str


class EducationThemeResponse(BaseModel):
    id: uuid.UUID
    theme: str
    link: str
    related_topics: Optional[List[str]] = None
    education_materials: List[EducationMaterialResponse] = Field(
        default_factory=list)


class EducationThemeWithMaterialsResponse(BaseModel):
    id: uuid.UUID
    theme: str
    link: str
    recommendations: List[ThemeRecommendationResponse] = Field(
        default_factory=list)
    education_materials: List[EducationMaterialResponse] = Field(
        default_factory=list)


class EducationThemeAdd(BaseModel):
    id: uuid.UUID
    theme: str
    link: str
    related_topics: Optional[List[str]] = None


class EducationProgressResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    education_material_id: uuid.UUID


class GetUserEducationProgressResponse(BaseModel):
    user_id: uuid.UUID
    education_material_id: uuid.UUID


class CompleteEducation(BaseModel):
    education_material_id: uuid.UUID


class CardAdd(BaseModel):
    id: uuid.UUID
    text: str
    number: int
    link_to_picture: Optional[str] = None
    education_material_id: uuid.UUID


class EducationMaterialAdd(BaseModel):
    id: uuid.UUID
    type: int
    number: int
    title: Optional[str] = None
    link_to_picture: Optional[str] = None
    education_theme_id: uuid.UUID
    subtitle: Optional[str] = None
