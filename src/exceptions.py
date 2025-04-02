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


class DiaryValidationError(MyAppException):
    detail = "Ошибка валидации данных дневника"


class DiaryTextEmptyError(DiaryValidationError):
    detail = "Текст записи не может быть пустым"


class DiaryTextTooLongError(DiaryValidationError):
    detail = "Текст записи слишком длинный"


class DiaryDateError(MyAppException):
    detail = "Ошибка даты записи"


class DiaryFutureDateError(DiaryDateError):
    detail = "Нельзя добавить запись на будущую дату"


class DiaryInvalidDateFormatError(DiaryDateError):
    detail = "Неверный формат даты"


class DiaryInvalidTimestampError(DiaryDateError):
    detail = "Неверное значение timestamp"


class DiaryValidationHTTPException(MyAppHTTPException):
    status_code = 422
    detail = "Ошибка валидации данных дневника"


class DiaryEntryNotFoundHTTPException(MyAppHTTPException):
    status_code = 404
    detail = "Запись дневника не найдена"


class DiaryDateHTTPException(MyAppHTTPException):
    status_code = 400
    detail = "Ошибка в параметрах даты"


class DiaryInternalErrorHTTPException(MyAppHTTPException):
    status_code = 500
    detail = "Внутренняя ошибка сервера при работе с дневником"


class DiaryTextEmptyHTTPException(MyAppHTTPException):
    status_code = 422
    detail = "Текст записи не может быть пустым"


class DiaryTextTooLongHTTPException(MyAppHTTPException):
    status_code = 422
    detail = "Текст записи слишком длинный"


class DiaryFutureDateHTTPException(MyAppHTTPException):
    status_code = 400
    detail = "Нельзя добавить запись на будущую дату"


class DiaryInvalidDateFormatHTTPException(MyAppHTTPException):
    status_code = 400
    detail = "Неверный формат даты"


class DiaryInvalidTimestampHTTPException(MyAppHTTPException):
    status_code = 400
    detail = "Неверное значение timestamp"


class MoodTrackerValidationError(MyAppException):
    detail = "Ошибка валидации данных трекера настроения"


class MoodScoreOutOfRangeError(MoodTrackerValidationError):
    detail = "Оценка настроения должна быть от 0 до 100"


class MoodTrackerDateFormatError(MoodTrackerValidationError):
    detail = "Неверный формат даты"


class MoodTrackerNotFoundError(MyAppException):
    detail = "Запись трекера настроения не найдена"


class MoodTrackerNotOwnedError(MyAppException):
    detail = "Запись не принадлежит текущему пользователю"


class MoodScoreOutOfRangeHTTPException(MyAppHTTPException):
    status_code = 422
    detail = "Оценка настроения должна быть от 0 до 100"


class MoodTrackerDateFormatHTTPException(MyAppHTTPException):
    status_code = 400
    detail = "Неверный формат даты"


class MoodTrackerNotFoundHTTPException(MyAppHTTPException):
    status_code = 404
    detail = "Запись трекера настроения не найдена"


class MoodTrackerNotOwnedHTTPException(MyAppHTTPException):
    status_code = 403
    detail = "Запись не принадлежит текущему пользователю"


class MoodTrackerInternalErrorHTTPException(MyAppHTTPException):
    status_code = 500
    detail = "Внутренняя ошибка сервера при работе с трекером настроения"


class MoodTrackerDateError(MyAppException):
    detail = "Ошибка даты трекера настроения"


class MoodTrackerFutureDateError(MoodTrackerDateError):
    detail = "Нельзя добавить запись на будущую дату"


class MoodTrackerFutureDateHTTPException(MyAppHTTPException):
    status_code = 400
    detail = "Нельзя добавить запись на будущую дату"


class InsufficientPermissionsException(MyAppException):
    detail = "У вас недостаточно прав для выполнения данной операции"


class ManagerNotFoundException(MyAppException):
    detail = "Менеджер не найден"


class ApplicationNotFoundException(MyAppException):
    detail = "Заявка не найдена"


class ApplicationForUserNotFound(MyAppException):
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


class ApplicationNotFoundHTTPException(MyAppHTTPException):
    status_code = 404
    detail = "Заявка не найдена"


class ApplicationForUserNotFoundHTTPException(MyAppHTTPException):
    status_code = 404
    detail = "Заявка для указанного пользователя не найдена"
