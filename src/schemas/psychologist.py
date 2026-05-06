import datetime
import uuid
from typing import Optional, List

from pydantic import BaseModel


class PsychologistResponse(BaseModel):
    username: str
    title: str
    document: str
    description: str
    city: str
    online: bool
    face_to_face: bool
    gender: str
    birth_date: datetime.date
    request: list[int]
    department: str


class EducationRequest(BaseModel):
    title: str
    document: str

class Inquiry(BaseModel):
    id: int
    text: str

class InquiryAddRequest(BaseModel):
    text: str

class BecomePsychologistRequest(BaseModel):
    username: Optional[str]
    birth_date: Optional[datetime.date]
    higher_education_university: Optional[str]
    higher_education_specialization: Optional[str]
    academic_degree: Optional[str] = None
    courses: Optional[str] = None
    work_format: Optional[str]
    association: Optional[str] = None
    inquiry_ids: List[int]

class InquiryShort(BaseModel):
    id: int
    text: str

    model_config = {"from_attributes": True}

class PsychologistResponseRequest(BaseModel):
    id: uuid.UUID
    username: Optional[str]
    birth_date: Optional[datetime.date]
    higher_education_university: Optional[str]
    higher_education_specialization: Optional[str]
    academic_degree: Optional[str] = None
    courses: Optional[str] = None
    work_format: Optional[str]
    association: Optional[str] = None
    inquiries: List[InquiryShort]

    model_config = {"from_attributes": True}
class UpdatePsychologistRequest(BaseModel):
    username: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    company: Optional[str] = None
    online: Optional[bool] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime.date] = None
    phone_number: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None
    face_to_face: Optional[bool] = None