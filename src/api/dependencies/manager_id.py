from typing import Annotated
from fastapi import Depends, Request

from src.exceptions import (
    IncorrectTokenException,
    IncorrectTokenHTTPException,
    NoAccessTokenHTTPException,
)
from src.services.auth import AuthService


def get_token(request: Request) -> str:
    token = request.cookies.get("access_token", None)
    if not token:
        raise NoAccessTokenHTTPException
    return token


def get_current_manager_id(token: str = Depends(get_token)) -> int:
    try:
        data = AuthService().decode_token(token)
    except IncorrectTokenException:
        raise IncorrectTokenHTTPException
    return data["user_id"]


ManagerIdDep = Annotated[int, Depends(get_current_manager_id)]
