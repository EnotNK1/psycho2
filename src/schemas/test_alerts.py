import datetime
import uuid

from pydantic import BaseModel


class TestAlert(BaseModel):
    client_id: uuid.UUID
    client_name: str
    test_id: uuid.UUID
    test_title: str
    test_result_id: uuid.UUID
    date: datetime.datetime
