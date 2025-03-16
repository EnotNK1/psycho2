from fastapi import APIRouter, HTTPException, Response
from pydantic import EmailStr

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
    UpdateUserRequest
from src.services.auth import AuthService
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.tasks.tasks import send_email_to_recover_password

router = APIRouter(prefix="/auth", tags=["Авторизация и аутентификация"])


@router.get("/me")
async def get_me(
        db: DBDep,
        user_id: UserIdDep,
):
    return await AuthService(db).get_one_or_none_user(id=user_id)


@router.post("/register")
async def register_user(db: DBDep, data: UserRequestAdd):
    try:
        await AuthService(db).register_user(data)
    except UserAlreadyExistsException:
        raise UserEmailAlreadyExistsHTTPException
    except PasswordDoNotMatchException:
        raise PasswordDoNotMatchHTTPException
    return {"status": "OK"}


@router.post("/login")
async def login_user(db: DBDep, data: UserRequestLogIn, response: Response):
    try:
        access_token = await AuthService(db).login_user(data)
    except EmailNotRegisteredException:
        raise EmailNotRegisteredHTTPException
    except IncorrectPasswordException:
        raise IncorrectPasswordHTTPException

    response.set_cookie("access_token", access_token)
    return {"access_token": access_token}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
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


@router.patch("/update")
async def update_user(
        db: DBDep,
        user_id: UserIdDep,
        data: UpdateUserRequest
):
    try:
        await AuthService(db).update_user(user_id, data)
        return {"status": "OK", "message": "User data updated successfully"}
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException()
    except SeveralObjectsFoundException:
        raise SeveralObjectsFoundHTTPException()
    except IncorrectTokenException:
        raise IncorrectTokenHTTPException()
    except MyAppException as e:
        raise e
    except Exception as e:
        raise MyAppHTTPException(detail="An unexpected error occurred: " + str(e))

