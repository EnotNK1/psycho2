from datetime import date
from fastapi import HTTPException


class MyAppException(Exception):
    detail = "Неожиданная ошибка"

    def __init__(self, *args, **kwargs):
        super().__init__(self.detail, *args, **kwargs)


class MyAppHTTPException(HTTPException):
    status_code = 500
    detail = None

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class ObjectNotFoundException(MyAppException):
    detail = "Объект не найден"


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
