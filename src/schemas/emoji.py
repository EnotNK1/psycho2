from pydantic import BaseModel

class Emoji(BaseModel):
    id: int
    text: str
