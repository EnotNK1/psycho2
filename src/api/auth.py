from fastapi import APIRouter, HTTPException, Response
from pydantic import EmailStr

from src.enums import DailyTaskType
from src.exceptions import (
    ObjectAlreadyExistsException,
    EmailNotRegisteredException,
    EmailNotRegisteredHTTPException,
    IncorrectPasswordException,
    IncorrectPasswordHTTPException,
    UserAlreadyExistsException,
    UserEmailAlreadyExistsHTTPException,
    PasswordDoNotMatchException,
    PasswordDoNotMatchHTTPException, ObjectNotFoundException, ObjectNotFoundHTTPException, IncorrectTokenException,
    IncorrectTokenHTTPException, MyAppException, SeveralObjectsFoundException, SeveralObjectsFoundHTTPException,
    MyAppHTTPException,
)
from src.schemas.users import UserRequestAdd, UserAdd, UserRequestLogIn, PasswordResetRequest, PasswordChangeRequest, \
    UpdateUserRequest, TokenResponse, RefreshTokenRequest
from src.services.auth import AuthService
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.services.daily_tasks import DailyTaskService
from src.tasks.tasks import send_email_to_recover_password

router = APIRouter(prefix="/auth", tags=["Авторизация и аутентификация"])


@router.get("/me",
            description="""
            Получение данных пользователя.\n
            В теле ответа возвращаются данные пользователя (id, username, email, city, company, 
            online, gender, birth_date, phone_number, description, is_active, department, face_to_face, role_id
            """)
async def get_me(
        db: DBDep,
        user_id: UserIdDep,
):
    return await AuthService(db).get_one_or_none_user(id=user_id)


@router.post("/register",
             description="""
             Регистрация нового пользователя.\n
             Входящие данные: email: user@example.com; username: string, birth_date: 2025-09-22; gender: male/female; 
             city: string; phone_number: string; password: string; confirm_password: string
             """,
             response_model=TokenResponse)
async def register_user(db: DBDep, data: UserRequestAdd):
    try:

        access_token, refresh_token = await AuthService(db).register_user(data)
    except UserAlreadyExistsException:
        raise UserEmailAlreadyExistsHTTPException
    except PasswordDoNotMatchException:
        raise PasswordDoNotMatchHTTPException
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/login",
             description="""Вход в аккаунт.\n 
             Входящие данные: email: user@example.com; password: string
             """,
             response_model=TokenResponse)
async def login_user(db: DBDep, data: UserRequestLogIn, response: Response):
    try:
        access_token, refresh_token = await AuthService(db).login_user(data)
    except EmailNotRegisteredException:
        raise EmailNotRegisteredHTTPException
    except IncorrectPasswordException:
        raise IncorrectPasswordHTTPException

    response.set_cookie("access_token", access_token)
    response.set_cookie("refresh_token", refresh_token, httponly=True)
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/token-auth",
             description="Вход по токену.",
             response_model=TokenResponse)
async def auth_with_token(db: DBDep, token: str, response: Response):
    try:
        payload = AuthService(db).decode_token(token)
        user_id = payload.get("user_id")
        user = await AuthService(db).get_one_or_none_user(id=user_id)
        if not user:
            raise IncorrectTokenHTTPException

        access_token, refresh_token = AuthService(db).create_tokens({
            "user_id": str(user.id),
            "role_id": user.role_id
        })

        response.set_cookie("access_token", access_token)
        response.set_cookie("refresh_token", refresh_token, httponly=True)
        return {"access_token": access_token, "refresh_token": refresh_token}
    except IncorrectTokenException:
        raise IncorrectTokenHTTPException


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(db: DBDep, data: RefreshTokenRequest, response: Response):
    try:
        access_token, refresh_token = await AuthService(db).refresh_tokens(data.refresh_token)
        response.set_cookie("access_token", access_token)
        response.set_cookie("refresh_token", refresh_token, httponly=True)
        return {"access_token": access_token, "refresh_token": refresh_token}
    except IncorrectTokenException:
        raise IncorrectTokenHTTPException


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"status": "OK"}


@router.post("/request-password-reset")
async def password_reset_request(db: DBDep, data: PasswordResetRequest):
    user = await AuthService(db).get_one_or_none_user(email=data.email)
    if not user:
        raise ObjectNotFoundHTTPException
    send_email_to_recover_password.delay(data.email)
    return {"status": "OK"}


@router.post("/password-reset")
async def password_change(db: DBDep, password_data: PasswordChangeRequest):
    try:
        await AuthService(db).change_password(password_data)
    except IncorrectTokenException:
        raise IncorrectTokenHTTPException
    except PasswordDoNotMatchException:
        raise PasswordDoNotMatchHTTPException
    return {"status": "OK"}


@router.patch("/update",
             description="""
             Редактирование данных пользователя.\n
             Входящие данные: username: string; description: string; city: string; company: string; online: 
             true/false;  gender: male/female; birth_date: 2025-09-22; phone_number: string
             """)
async def update_user(
        db: DBDep,
        user_id: UserIdDep,
        data: UpdateUserRequest
):
    try:
        await AuthService(db).update_user(user_id, data)
        return {"status": "OK"}
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException()
    except SeveralObjectsFoundException:
        raise SeveralObjectsFoundHTTPException()
    except IncorrectTokenException:
        raise IncorrectTokenHTTPException()
    except MyAppException as e:
        raise e
    except Exception as e:
        raise MyAppHTTPException(
            detail="An unexpected error occurred: " + str(e))
