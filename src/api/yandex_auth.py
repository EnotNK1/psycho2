from fastapi import APIRouter, Response
from fastapi.responses import RedirectResponse
from src.api.dependencies.db import DBDep
from src.services.auth import AuthService
from src.schemas.users import TokenResponse
import secrets
import httpx

from src.config import settings

router = APIRouter(prefix="/yandex", tags=["Авторизация Яндекс"])

YANDEX_AUTH_URL = "https://oauth.yandex.ru/authorize"
REDIRECT_URI = "https://xn--d1acsjd4h.tech"


async def get_yandex_user(access_token: str) -> dict:
    print(access_token)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://login.yandex.ru/info",
            headers={
                "Authorization": f"OAuth {access_token}"
            }
        )

    return response.json()


async def exchange_code(code: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth.yandex.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.ClientID,
                "client_secret": settings.ClientSecret,
                "redirect_uri": REDIRECT_URI,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

    data = response.json()

    if "access_token" not in data:
        raise Exception(data)

    return data["access_token"]


@router.get("/login")
def yandex_login():

    url = (
        f"{YANDEX_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={settings.ClientID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=login:email login:info"
        f"&force_confirm=1"
    )

    return RedirectResponse(url)


@router.get("/callback/token")
async def yandex_callback_token(
    token: str,
    db: DBDep,
    response: Response
):
    yandex_user = await get_yandex_user(token)

    access_token, refresh_token = await AuthService(db).oauth_login(
        email=yandex_user["default_email"],
        username=yandex_user["login"],
        gender=yandex_user["sex"],
    )

    response.set_cookie("access_token", access_token)
    response.set_cookie("refresh_token", refresh_token, httponly=True)

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.get("/callback/code")
async def yandex_callback_code(
    code: str,
    db: DBDep,
    response: Response
):
    yandex_token = await exchange_code(code)
    yandex_user = await get_yandex_user(yandex_token)

    access_token, refresh_token = await AuthService(db).oauth_login(
        email=yandex_user["default_email"],
        username=yandex_user["login"],
        gender=yandex_user["sex"],
    )

    response.set_cookie("access_token", access_token)
    response.set_cookie("refresh_token", refresh_token, httponly=True)

    return {"access_token": access_token, "refresh_token": refresh_token}
