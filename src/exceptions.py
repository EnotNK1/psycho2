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


class InvalidPeriodHTTPException(HTTPException):
    status_code = 400
    detail = None

    def __init__(self, detail: str = "Неверный период"):
        super().__init__(status_code=self.status_code, detail=self.detail)


class ObjectNotFoundException(MyAppException):
    detail = "Объект не найден"


class SeveralObjectsFoundException(MyAppException):
    detail = "Найдено несколько объектов"


class ObjectAlreadyExistsException(MyAppException):
    detail = "Похожий объект уже существует"

class ObjectAlreadyExistsHTTPException(MyAppHTTPException):
    status_code = 409
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
    status_code = 401
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


class ValidationError(MyAppException):
    detail = "Ошибка валидации данных"


class TextEmptyError(ValidationError):
    detail = "Текст записи не может быть пустым"


class TextTooLongError(ValidationError):
    detail = "Текст записи слишком длинный"


class DateError(MyAppException):
    detail = "Ошибка даты записи"


class FutureDateError(DateError):
    detail = "Нельзя добавить запись на будущую дату"


class InvalidDateFormatError(DateError):
    detail = "Неверный формат даты"


class InvalidTimestampError(DateError):
    detail = "Неверное значение timestamp"


class InternalErrorHTTPException(MyAppHTTPException):
    status_code = 500
    detail = "Внутренняя ошибка сервера"


class TextEmptyHTTPException(MyAppHTTPException):
    status_code = 422
    detail = "Текст записи не может быть пустым"


class TextTooLongHTTPException(MyAppHTTPException):
    status_code = 422
    detail = "Текст записи слишком длинный"


class FutureDateHTTPException(MyAppHTTPException):
    status_code = 400
    detail = "Нельзя добавить запись на будущую дату"


class InvalidDateFormatHTTPException(MyAppHTTPException):
    status_code = 400
    detail = "Неверный формат даты"


class InvalidTimestampHTTPException(MyAppHTTPException):
    status_code = 400
    detail = "Неверное значение timestamp"


class ScoreOutOfRangeError(ValidationError):
    detail = "Оценка настроения должна быть от 0 до 100"


class NotOwnedError(MyAppException):
    detail = "Запись не принадлежит текущему пользователю"


class ScoreOutOfRangeHTTPException(MyAppHTTPException):
    status_code = 422
    detail = "Оценка настроения должна быть от 0 до 100"


class NotOwnedHTTPException(MyAppHTTPException):
    status_code = 403
    detail = "Запись не принадлежит текущему пользователю"


class InsufficientPermissionsException(MyAppException):
    detail = "У вас недостаточно прав для выполнения данной операции"


class ManagerNotFoundException(MyAppException):
    detail = "Менеджер не найден"


class ForUserNotFoundException(MyAppException):
    detail = "Заявка для указанного пользователя не найдена"


class UserNotFoundException(MyAppException):
    detail = "Такого пользователя не существует"


class UserNotFoundHTTPException(MyAppHTTPException):
    status_code = 404
    detail = "Такого пользователя не существует"


class InsufficientPermissionsHTTPException(MyAppHTTPException):
    status_code = 403
    detail = "У вас недостаточно прав для выполнения данной операции"


class ManagerNotFoundHTTPException(MyAppHTTPException):
    status_code = 404
    detail = "Менеджер не найден"


class ForUserNotFoundHTTPException(MyAppHTTPException):
    status_code = 404
    detail = "Заявка для указанного пользователя не найдена"

class InvalidAnswersCountError(MyAppHTTPException):
    status_code = 400
    detail = "Неверное количество ответов"

class ResultsScaleMismatchError(MyAppHTTPException):
    status_code = 500
    detail = "Количество результатов не соответствует количеству шкал"

class ScoreOutOfBoundsError(MyAppHTTPException):
    status_code = 400
    detail = "Результат вне границ шкалы"

class InvalidAnswersCountHTTPError(MyAppHTTPException):
    status_code = 400
    detail = "Неверное количество ответов"

class ResultsScaleMismatchHTTPError(MyAppHTTPException):
    status_code = 500
    detail = "Количество результатов не соответствует количеству шкал"

class ScoreOutOfBoundsHTTPError(MyAppHTTPException):
    status_code = 400
    detail = "Результат вне границ шкалы"

class InvalidEmojiIdException(MyAppException):
    detail = "ID emoji вне допустимых значений: (1-10)"

class InvalidEmojiIdHTTPException(MyAppHTTPException):
    status_code = 400
    detail = "ID emoji вне допустимых значений: (1-10)"