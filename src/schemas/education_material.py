from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class CardResponse(BaseModel):
    id: uuid.UUID
    text: str
    number: int
    link_to_picture: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CardAdd(BaseModel):
    id: uuid.UUID
    text: str
    number: int
    link_to_picture: Optional[str] = None
    education_material_id: uuid.UUID


class CardCreate(BaseModel):
    text: str
    number: int
    link_to_picture: Optional[str] = None


class CardUpdate(BaseModel):
    text: Optional[str] = None
    number: Optional[int] = None
    link_to_picture: Optional[str] = None
    education_material_id: Optional[uuid.UUID] = None


class EducationMaterialResponse(BaseModel):
    id: uuid.UUID
    type: int
    number: int
    title: Optional[str] = None
    link_to_picture: Optional[str] = None
    subtitle: Optional[str] = None
    cards: List[CardResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class EducationMaterialAdd(BaseModel):
    id: uuid.UUID
    type: int
    number: int
    title: Optional[str] = None
    link_to_picture: Optional[str] = None
    education_theme_id: uuid.UUID
    subtitle: Optional[str] = None


class EducationMaterialCreate(BaseModel):
    type: int
    number: int
    title: Optional[str] = None
    link_to_picture: Optional[str] = None
    subtitle: Optional[str] = None


class EducationMaterialUpdate(BaseModel):
    type: Optional[int] = None
    number: Optional[int] = None
    title: Optional[str] = None
    link_to_picture: Optional[str] = None
    education_theme_id: Optional[uuid.UUID] = None
    subtitle: Optional[str] = None


class ThemeRecommendationResponse(BaseModel):
    id: uuid.UUID
    theme: str
    link: str
    link_to_picture: Optional[str] = None
    tags: Optional[List[str]] = None


class EducationThemeResponse(BaseModel):
    id: uuid.UUID
    theme: str
    link: str
    link_to_picture: Optional[str] = None
    tags: Optional[List[str]] = None
    education_materials: List[EducationMaterialResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class EducationThemeWithMaterialsResponse(BaseModel):
    id: uuid.UUID
    theme: str
    link_to_picture: Optional[str] = None
    link: str
    recommendations: List[ThemeRecommendationResponse] = Field(default_factory=list)
    education_materials: List[EducationMaterialResponse] = Field(default_factory=list)


class EducationThemeAdd(BaseModel):
    id: uuid.UUID
    theme: str
    link: str
    link_to_picture: Optional[str] = None
    tags: Optional[List[str]] = None
    related_topics: Optional[List[str]] = None


class EducationThemeCreate(BaseModel):
    theme: str
    link: str
    link_to_picture: Optional[str] = None
    tags: Optional[List[str]] = None
    related_topics: Optional[List[str]] = None


class EducationThemeUpdate(BaseModel):
    theme: Optional[str] = None
    link: Optional[str] = None
    link_to_picture: Optional[str] = None
    tags: Optional[List[str]] = None
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


class CompleteEducationTheme(BaseModel):
    education_theme_id: uuid.UUID
