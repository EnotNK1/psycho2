from pydantic import BaseModel, EmailStr, Field


class YandexTokenRequest(BaseModel):
    token: str = Field(min_length=1, max_length=4096, repr=False)


class YandexProfile(BaseModel):
    id: str = Field(min_length=1, max_length=255)
    client_id: str = Field(min_length=1)
    default_email: EmailStr
    login: str = Field(default="", max_length=255)
    display_name: str = Field(default="", max_length=255)
    sex: str = ""
