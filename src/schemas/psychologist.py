import datetime
from typing import Optional

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


class BecomePsychologistRequest(BaseModel):
    username: str
    description: str
    city: str
    company: str
    online: bool
    gender: str
    birth_date: datetime.date
    is_active: bool
    department: str
    face_to_face: bool

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