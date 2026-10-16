from typing import Annotated
import uuid

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


def get_current_user_id(token: str = Depends(get_token)) -> uuid.UUID:
    try:
        data = AuthService().decode_token(token)
        return uuid.UUID(str(data["user_id"]))
    except IncorrectTokenException:
        raise IncorrectTokenHTTPException
    except (KeyError, ValueError, TypeError):
        raise IncorrectTokenHTTPException


UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
