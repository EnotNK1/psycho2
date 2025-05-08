from typing import Annotated
from fastapi import Depends, Request

from src.exceptions import (
    IncorrectTokenException,
    IncorrectTokenHTTPException,
    NoAccessTokenHTTPException, AccessDeniedHTTPException,
)
from src.services.auth import AuthService


def get_token(request: Request) -> str:
    token = request.cookies.get("access_token", None)
    if not token:
        raise NoAccessTokenHTTPException
    return token


def get_current_manager_id(token: str = Depends(get_token)) -> int:
    try:
        # Декодируем токен
        data = AuthService().decode_token(token)
        user_id = data["user_id"]
        role_id = data.get("role_id")

        if role_id != 2:
            raise AccessDeniedHTTPException(detail="Доступ запрещён: требуется роль менеджера")

        return user_id

    except IncorrectTokenException:
        raise IncorrectTokenHTTPException

ManagerIdDep = Annotated[int, Depends(get_current_manager_id)]
