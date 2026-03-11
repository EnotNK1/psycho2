from typing import Optional

from pydantic import BaseModel
import datetime
import uuid


class OntologyEntry(BaseModel):
    id: uuid.UUID
    type: str
    created_at: datetime.datetime
    destination_id: uuid.UUID
    user_id: uuid.UUID




