from pydantic import BaseModel


class Inquiry(BaseModel):
    id: int
    text: str