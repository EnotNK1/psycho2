from datetime import datetime, timezone, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import select, func

from src.api import yandex_auth
from src.config import settings
from src.models.users import UsersOrm
from src.schemas.yandex import YandexProfile
from src.services import yandex


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(settings, "YANDEX_CLIENT_ID", "test-compas-client")
    monkeypatch.setattr(settings, "YANDEX_CLIENT_SECRET", "test-compas-secret")
    monkeypatch.setattr(
        settings, "YANDEX_REDIRECT_URI", "http://127.0.0.1:8001/yandex/callback/code"
    )


def fake_profile(email="new.yandex@example.com", subject="yandex-123", **kwargs):
    return YandexProfile(
        id=subject,
        client_id="test-compas-client",
        default_email=email,
        login="Yandex Login",
        **kwargs,
    )


def mock_profile(monkeypatch, profile):
    async def get(token):
        return profile

    monkeypatch.setattr(yandex_auth, "get_yandex_user", get)


def test_disabled_is_visible_but_returns_clear_503(sandbox, monkeypatch):
    monkeypatch.setattr(settings, "YANDEX_CLIENT_ID", "")
    monkeypatch.setattr(settings, "YANDEX_CLIENT_SECRET", "")
    assert "/yandex/login" in sandbox.http.get("/openapi.json").json()["paths"]
    response = sandbox.http.get("/yandex/login", follow_redirects=False)
    assert response.status_code == 503
    assert "YANDEX_CLIENT_ID" in response.json()["detail"]


def test_login_redirect_state_pkce_cookie(sandbox, configured):
    response = sandbox.http.get("/yandex/login", follow_redirects=False)
    assert response.status_code == 302
    url = urlparse(response.headers["location"])
    assert url.scheme == "https" and url.netloc == "oauth.yandex.ru"
    query = parse_qs(url.query)
    assert query["client_id"] == ["test-compas-client"]
    assert query["redirect_uri"] == [settings.YANDEX_REDIRECT_URI]
    assert query["code_challenge_method"] == ["S256"]
    assert "login:email" in query["scope"][0]
    assert "test-compas-secret" not in response.headers["location"]
    cookie = response.cookies[yandex_auth.STATE_COOKIE]
    saved = yandex_auth.state_serializer().loads(cookie, max_age=600)
    assert saved["state"] == query["state"][0] and len(saved["verifier"]) >= 43
    assert "HttpOnly" in response.headers["set-cookie"]
    second = sandbox.http.get("/yandex/login", follow_redirects=False)
    assert (
        parse_qs(urlparse(second.headers["location"]).query)["state"] != query["state"]
    )


@pytest.mark.parametrize("state", [None, "wrong", "несовпадение"])
def test_bad_state_does_not_call_provider(sandbox, configured, monkeypatch, state):
    async def forbidden(*args):
        raise AssertionError("provider must not be called")

    monkeypatch.setattr(yandex_auth, "exchange_code", forbidden)
    sandbox.http.get("/yandex/login", follow_redirects=False)
    params = {"code": "fake-code"}
    if state is not None:
        params["state"] = state
    assert sandbox.http.get("/yandex/callback/code", params=params).status_code == 400


def test_callback_rejects_missing_tampered_expired_state(
    sandbox, configured, monkeypatch
):
    params = {"code": "fake", "state": "expected"}
    assert sandbox.http.get("/yandex/callback/code", params=params).status_code == 400
    sandbox.http.cookies.set(yandex_auth.STATE_COOKIE, "tampered")
    assert sandbox.http.get("/yandex/callback/code", params=params).status_code == 400
    sandbox.http.cookies.clear()

    class OldSerializer(URLSafeTimedSerializer):
        default_signer = type(
            "OldSigner",
            (URLSafeTimedSerializer.default_signer,),
            {
                "get_timestamp": lambda self: int(
                    (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()
                )
            },
        )

    old = OldSerializer(settings.JWT_SECRET_KEY, salt="compas-yandex-oauth-v1")
    sandbox.http.cookies.set(
        yandex_auth.STATE_COOKIE, old.dumps({"state": "expected", "verifier": "v" * 48})
    )
    assert sandbox.http.get("/yandex/callback/code", params=params).status_code == 400


def test_code_flow_creates_user_and_does_not_duplicate(
    sandbox, configured, monkeypatch
):
    calls = []

    async def exchange(code, verifier):
        calls.append((code, verifier))
        return "fake-provider-token"

    monkeypatch.setattr(yandex_auth, "exchange_code", exchange)
    mock_profile(monkeypatch, fake_profile())
    login = sandbox.http.get("/yandex/login", follow_redirects=False)
    state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
    response = sandbox.http.get(
        "/yandex/callback/code", params={"code": "test-code", "state": state}
    )
    assert response.status_code == 200, response.text
    assert calls[0][0] == "test-code"
    assert "compas_access_token" in response.cookies
    assert response.headers["cache-control"] == "no-store"
    assert "fake-provider-token" not in response.text
    assert sandbox.http.get("/auth/me").json()["role_id"] == 1
    user = sandbox.session.scalar(
        select(UsersOrm).where(UsersOrm.yandex_id == "yandex-123")
    )
    assert user.hashed_password is None and user.gender == "not specified"
    sandbox.http.cookies.clear()
    again = sandbox.http.post(
        "/yandex/callback/token", json={"token": "fake-provider-token"}
    )
    assert again.status_code == 200
    assert sandbox.session.scalar(select(func.count()).select_from(UsersOrm)) == 6
    assert (
        sandbox.http.post(
            "/auth/login",
            json={"email": "new.yandex@example.com", "password": "Anything123!"},
        ).status_code
        == 401
    )


def test_matching_email_requires_authenticated_link_and_preserves_role(
    sandbox, configured, monkeypatch
):
    mock_profile(monkeypatch, fake_profile(email="psychologist@example.com"))
    assert (
        sandbox.http.post("/yandex/callback/token", json={"token": "fake"}).status_code
        == 409
    )
    assert sandbox.http.post("/yandex/link", json={"token": "fake"}).status_code == 401
    sandbox.login("stranger")
    assert sandbox.http.post("/yandex/link", json={"token": "fake"}).status_code == 409
    sandbox.login("psychologist")
    assert sandbox.http.post("/yandex/link", json={"token": "fake"}).status_code == 200
    sandbox.http.cookies.clear()
    assert (
        sandbox.http.post("/yandex/callback/token", json={"token": "fake"}).status_code
        == 200
    )
    assert sandbox.http.get("/auth/me").json()["role_id"] == 2
    mock_profile(
        monkeypatch,
        fake_profile(email="psychologist@example.com", subject="another-id"),
    )
    assert sandbox.http.post("/yandex/link", json={"token": "fake"}).status_code == 409


def test_denial_and_legacy_get_token(sandbox, configured):
    login = sandbox.http.get("/yandex/login", follow_redirects=False)
    state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
    response = sandbox.http.get(
        "/yandex/callback/code", params={"state": state, "error": "access_denied"}
    )
    assert response.status_code == 400
    assert yandex_auth.STATE_COOKIE not in sandbox.http.cookies
    assert (
        sandbox.http.get(
            "/yandex/callback/token", params={"token": "do-not-accept-in-url"}
        ).status_code
        == 405
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,body,expected",
    [
        (401, {}, 401),
        (503, {}, 502),
        (200, {"id": "1"}, 400),
        (
            200,
            {"id": "1", "client_id": "other", "default_email": "ok@example.com"},
            401,
        ),
    ],
)
async def test_provider_profile_errors(configured, monkeypatch, status, body, expected):
    original = httpx.AsyncClient
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status, json=body)

    monkeypatch.setattr(
        yandex.httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )
    with pytest.raises(Exception) as error:
        await yandex.get_yandex_user("private-provider-token")
    assert error.value.status_code == expected
    assert requests[0].headers["Authorization"] == "OAuth private-provider-token"
    assert "private-provider-token" not in str(requests[0].url)


@pytest.mark.asyncio
async def test_code_exchange_pkce_and_token_response(configured, monkeypatch):
    original = httpx.AsyncClient
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"access_token": "private-access-token"})

    monkeypatch.setattr(
        yandex.httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )
    assert (
        await yandex.exchange_code("code-123", "verifier-123") == "private-access-token"
    )
    params = parse_qs(requests[0].content.decode())
    assert params["code"] == ["code-123"]
    assert params["code_verifier"] == ["verifier-123"]
    assert params["redirect_uri"] == [settings.YANDEX_REDIRECT_URI]
    assert "test-compas-secret" not in str(requests[0].url)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,body,expected", [(400, {}, 400), (503, {}, 502), (200, {}, 502)]
)
async def test_code_exchange_errors(configured, monkeypatch, status, body, expected):
    original = httpx.AsyncClient

    def handler(request):
        return httpx.Response(status, json=body)

    monkeypatch.setattr(
        yandex.httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )
    with pytest.raises(Exception) as error:
        await yandex.exchange_code("code-123", "verifier-123")
    assert error.value.status_code == expected
    assert "test-compas-secret" not in str(error.value.detail)
