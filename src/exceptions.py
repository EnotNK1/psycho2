from datetime import date
from fastapi import HTTPException


class MyAppException(Exception):
    detail = "Неожиданная ошибка"

    def __init__(self, *args, **kwargs):
        super().__init__(self.detail, *args, **kwargs)


class MyAppHTTPException(HTTPException):
    status_code = 500
    detail: str

    def __init__(self, detail: str):
        super().__init__(status_code=self.status_code, detail=detail)
        self.detail = detail


class ObjectNotFoundException(MyAppException):
    detail = "Объект не найден"


class SeveralObjectsFoundException(MyAppException):
    detail = "Найдено несколько объектов"


class ObjectAlreadyExistsException(MyAppException):
    detail = "Похожий объект уже существует"


class IncorrectTokenException(MyAppException):
    detail = "Некорректный токен"


class EmailNotRegisteredException(MyAppException):
    detail = "Пользователь с таким email не зарегистрирован"


class IncorrectPasswordException(MyAppException):
    detail = "Пароль неверный"


class PasswordDoNotMatchException(MyAppException):
    detail = "Пароли не совпадают"


class UserAlreadyExistsException(MyAppException):
    detail = "Пользователь уже существует"


class IncorrectTokenHTTPException(MyAppHTTPException):
    detail = "Некорректный токен"


class ObjectNotFoundHTTPException(MyAppHTTPException):
    status_code = 404
    detail = "Объект не найден"


class SeveralObjectsFoundHTTPException(MyAppHTTPException):
    status_code = 400
    detail = "Найдено несколько объектов"


class EmailNotRegisteredHTTPException(MyAppHTTPException):
    status_code = 401
    detail = "Пользователь с таким email не зарегистрирован"


class PasswordDoNotMatchHTTPException(MyAppHTTPException):
    status_code = 401
    detail = "Пароли не совпадают"


class UserEmailAlreadyExistsHTTPException(MyAppHTTPException):
    status_code = 409
    detail = "Пользователь с такой почтой уже существует"


class IncorrectPasswordHTTPException(MyAppHTTPException):
    status_code = 401
    detail = "Пароль неверный"


class NoAccessTokenHTTPException(MyAppHTTPException):
    status_code = 401
    detail = "Вы не предоставили токен доступа"


class AccessDeniedHTTPException(MyAppHTTPException):
    status_code = 403  # 403 Forbidden
    detail = "Доступ запрещён: недостаточно прав"
