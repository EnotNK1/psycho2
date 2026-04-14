import pytest

import src.api.auth as auth_api_module
from autotest4.factories.auth import (
    SECOND_USER_ID,
    USER_ID,
    build_login_payload,
    build_password_change_payload,
    build_password_reset_request,
    build_refresh_payload,
    build_register_payload,
    build_update_user_payload,
    build_test_result,
    make_user,
)
from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.exceptions import (
    EmailNotRegisteredException,
    IncorrectPasswordException,
    IncorrectTokenException,
    MyAppException,
    ObjectNotFoundException,
    PasswordDoNotMatchException,
    SeveralObjectsFoundException,
    UserAlreadyExistsException,
)

def header_values(response, name):
    getter = getattr(response.headers, "get_list", None)
    if getter is not None:
        return getter(name)
    return response.headers.getlist(name)


class DummyAuthApiService:
    me_response = None
    delete_response = {"status": "OK"}
    register_response = ("access-token", "refresh-token")
    login_response = ("access-token", "refresh-token")
    refresh_response = ("new-access-token", "new-refresh-token")
    token_payload = {"user_id": str(USER_ID)}
    token_user = None
    token_create_response = ("token-access", "token-refresh")
    burnout_response = 0.42
    raise_on_me = None
    raise_on_delete = None
    raise_on_register = None
    raise_on_login = None
    raise_on_decode = None
    raise_on_refresh = None
    raise_on_change_password = None
    raise_on_update = None
    raise_on_burnout = None
    last_register_data = None
    last_login_data = None
    last_refresh_token = None
    last_change_password = None
    last_update_args = None
    last_get_one_or_none_filters = None
    last_delete_filters = None
    last_burnout_input = None

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.me_response = None
        cls.delete_response = {"status": "OK"}
        cls.register_response = ("access-token", "refresh-token")
        cls.login_response = ("access-token", "refresh-token")
        cls.refresh_response = ("new-access-token", "new-refresh-token")
        cls.token_payload = {"user_id": str(USER_ID)}
        cls.token_user = None
        cls.token_create_response = ("token-access", "token-refresh")
        cls.burnout_response = 0.42
        cls.raise_on_me = None
        cls.raise_on_delete = None
        cls.raise_on_register = None
        cls.raise_on_login = None
        cls.raise_on_decode = None
        cls.raise_on_refresh = None
        cls.raise_on_change_password = None
        cls.raise_on_update = None
        cls.raise_on_burnout = None
        cls.last_register_data = None
        cls.last_login_data = None
        cls.last_refresh_token = None
        cls.last_change_password = None
        cls.last_update_args = None
        cls.last_get_one_or_none_filters = None
        cls.last_delete_filters = None
        cls.last_burnout_input = None

    async def get_one_or_none_user(self, **filter_by):
        if type(self).raise_on_me:
            raise type(self).raise_on_me
        type(self).last_get_one_or_none_filters = filter_by
        if filter_by.get("id") == type(self).token_payload.get("user_id"):
            return type(self).token_user
        return type(self).me_response

    async def delete_user(self, **filter_by):
        if type(self).raise_on_delete:
            raise type(self).raise_on_delete
        type(self).last_delete_filters = filter_by
        return type(self).delete_response

    async def register_user(self, data):
        if type(self).raise_on_register:
            raise type(self).raise_on_register
        type(self).last_register_data = data
        return type(self).register_response

    async def login_user(self, data):
        if type(self).raise_on_login:
            raise type(self).raise_on_login
        type(self).last_login_data = data
        return type(self).login_response

    def decode_token(self, token):
        if type(self).raise_on_decode:
            raise type(self).raise_on_decode
        return type(self).token_payload

    def create_tokens(self, data):
        return type(self).token_create_response

    async def refresh_tokens(self, refresh_token):
        if type(self).raise_on_refresh:
            raise type(self).raise_on_refresh
        type(self).last_refresh_token = refresh_token
        return type(self).refresh_response

    async def change_password(self, password_data):
        if type(self).raise_on_change_password:
            raise type(self).raise_on_change_password
        type(self).last_change_password = password_data

    async def update_user(self, user_id, data):
        if type(self).raise_on_update:
            raise type(self).raise_on_update
        type(self).last_update_args = (user_id, data)

    async def burnout_calculate(self, test_results):
        if type(self).raise_on_burnout:
            raise type(self).raise_on_burnout
        type(self).last_burnout_input = test_results
        return type(self).burnout_response


class DummyTestService:
    response = []
    raise_on_get = None
    last_args = None

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.response = []
        cls.raise_on_get = None
        cls.last_args = None

    async def get_test_result_by_user_and_test(self, test_id, user_id):
        if type(self).raise_on_get:
            raise type(self).raise_on_get
        type(self).last_args = (test_id, user_id)
        return type(self).response


class DummyDelay:
    calls = []

    @classmethod
    def reset(cls):
        cls.calls = []

    @classmethod
    def delay(cls, email):
        cls.calls.append(email)


@pytest.fixture
def auth_api_client_factory(api_client_factory, monkeypatch):
    DummyAuthApiService.reset()
    DummyTestService.reset()
    DummyDelay.reset()
    monkeypatch.setattr(auth_api_module, "AuthService", DummyAuthApiService)
    monkeypatch.setattr(auth_api_module, "TestService", DummyTestService)
    monkeypatch.setattr(auth_api_module.send_email_to_recover_password, "delay", DummyDelay.delay)

    def _factory(user_id=USER_ID):
        fake_db = object()

        async def override_get_db():
            yield fake_db

        def override_get_current_user_id():
            return user_id

        async def _client():
            async for async_client, _ in api_client_factory(
                auth_api_module.router,
                dependency_overrides={
                    get_db: override_get_db,
                    get_current_user_id: override_get_current_user_id,
                },
            ):
                yield async_client, fake_db

        return _client()

    return _factory


@pytest.mark.asyncio
async def test_get_me_returns_user_payload(auth_api_client_factory):
    DummyAuthApiService.me_response = make_user()

    async for client, _ in auth_api_client_factory():
        response = await client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(USER_ID)
    assert DummyAuthApiService.last_get_one_or_none_filters == {"id": USER_ID}


@pytest.mark.asyncio
async def test_get_me_returns_500_when_service_fails(auth_api_client_factory):
    DummyAuthApiService.raise_on_me = RuntimeError("db unavailable")

    async for client, _ in auth_api_client_factory():
        response = await client.get("/auth/me")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_delete_me_returns_service_payload(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.delete("/auth/delete")

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    assert DummyAuthApiService.last_delete_filters == {"id": USER_ID}


@pytest.mark.asyncio
async def test_delete_me_returns_500_when_service_fails(auth_api_client_factory):
    DummyAuthApiService.raise_on_delete = RuntimeError("delete failed")

    async for client, _ in auth_api_client_factory():
        response = await client.delete("/auth/delete")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_register_returns_tokens(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/register", json=build_register_payload())

    assert response.status_code == 200
    assert response.json() == {"access_token": "access-token", "refresh_token": "refresh-token"}
    assert DummyAuthApiService.last_register_data.email == "user@example.com"


@pytest.mark.asyncio
async def test_register_maps_user_exists(auth_api_client_factory):
    DummyAuthApiService.raise_on_register = UserAlreadyExistsException()

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/register", json=build_register_payload())

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_maps_password_mismatch(auth_api_client_factory):
    DummyAuthApiService.raise_on_register = PasswordDoNotMatchException()

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/register", json=build_register_payload())

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_returns_500_for_unexpected_service_error(auth_api_client_factory):
    DummyAuthApiService.raise_on_register = RuntimeError("unexpected register error")

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/register", json=build_register_payload())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_register_returns_422_for_invalid_email(auth_api_client_factory):
    payload = build_register_payload(email="bad-email")

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/register", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "missing_field",
    [
        "email",
        "username",
        "birth_date",
        "gender",
        "city",
        "phone_number",
        "password",
        "confirm_password",
    ],
)
async def test_register_returns_422_when_required_field_missing(
    auth_api_client_factory,
    missing_field,
):
    payload = build_register_payload()
    payload.pop(missing_field)

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/register", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_returns_422_for_invalid_birth_date(auth_api_client_factory):
    payload = build_register_payload(birth_date="not-a-date")

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/register", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_returns_422_for_empty_body(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/register", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_returns_tokens_and_sets_cookies(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/login", json=build_login_payload())

    assert response.status_code == 200
    assert response.json() == {"access_token": "access-token", "refresh_token": "refresh-token"}
    cookie_header = header_values(response, "set-cookie")
    assert any("access_token=access-token" in item for item in cookie_header)
    assert any("refresh_token=refresh-token" in item for item in cookie_header)
    assert any("refresh_token=refresh-token" in item and "HttpOnly" in item for item in cookie_header)


@pytest.mark.asyncio
async def test_login_maps_unknown_email(auth_api_client_factory):
    DummyAuthApiService.raise_on_login = EmailNotRegisteredException()

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/login", json=build_login_payload())

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_maps_incorrect_password(auth_api_client_factory):
    DummyAuthApiService.raise_on_login = IncorrectPasswordException()

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/login", json=build_login_payload())

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_returns_500_for_unexpected_service_error(auth_api_client_factory):
    DummyAuthApiService.raise_on_login = RuntimeError("unexpected login error")

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/login", json=build_login_payload())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_login_returns_422_for_invalid_email(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/login", json=build_login_payload(email="bad-email"))

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_field", ["email", "password"])
async def test_login_returns_422_when_required_field_missing(auth_api_client_factory, missing_field):
    payload = build_login_payload()
    payload.pop(missing_field)

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/login", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_returns_422_for_empty_body(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/login", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_token_auth_returns_tokens_for_existing_user(auth_api_client_factory):
    DummyAuthApiService.token_payload = {"user_id": str(USER_ID)}
    DummyAuthApiService.token_user = make_user()

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/token-auth?token=valid-token")

    assert response.status_code == 200
    assert response.json() == {"access_token": "token-access", "refresh_token": "token-refresh"}
    cookie_header = header_values(response, "set-cookie")
    assert any("access_token=token-access" in item for item in cookie_header)
    assert any("refresh_token=token-refresh" in item and "HttpOnly" in item for item in cookie_header)


@pytest.mark.asyncio
async def test_token_auth_maps_incorrect_token(auth_api_client_factory):
    DummyAuthApiService.raise_on_decode = IncorrectTokenException()

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/token-auth?token=bad-token")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_auth_returns_500_when_user_lookup_fails(auth_api_client_factory):
    DummyAuthApiService.raise_on_me = RuntimeError("lookup failed")

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/token-auth?token=valid-token")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_token_auth_returns_422_when_token_query_missing(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/token-auth")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_token_auth_returns_401_when_user_not_found(auth_api_client_factory):
    DummyAuthApiService.token_payload = {"user_id": str(USER_ID)}
    DummyAuthApiService.token_user = None

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/token-auth?token=valid-token")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_returns_new_tokens(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/refresh-token", json=build_refresh_payload())

    assert response.status_code == 200
    assert response.json() == {"access_token": "new-access-token", "refresh_token": "new-refresh-token"}
    assert DummyAuthApiService.last_refresh_token == "refresh-token"
    cookie_header = header_values(response, "set-cookie")
    assert any("access_token=new-access-token" in item for item in cookie_header)
    assert any("refresh_token=new-refresh-token" in item and "HttpOnly" in item for item in cookie_header)


@pytest.mark.asyncio
async def test_refresh_token_maps_incorrect_token(auth_api_client_factory):
    DummyAuthApiService.raise_on_refresh = IncorrectTokenException()

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/refresh-token", json=build_refresh_payload())

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_returns_500_for_unexpected_service_error(auth_api_client_factory):
    DummyAuthApiService.raise_on_refresh = RuntimeError("refresh failed")

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/refresh-token", json=build_refresh_payload())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_refresh_token_returns_422_when_refresh_token_missing(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/refresh-token", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_refresh_token_returns_422_for_empty_body(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/refresh-token")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_logout_clears_cookies(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    cookie_header = header_values(response, "set-cookie")
    assert any("access_token=" in item and "Max-Age=0" in item for item in cookie_header)
    assert any("refresh_token=" in item and "Max-Age=0" in item for item in cookie_header)


@pytest.mark.asyncio
async def test_password_reset_request_enqueues_email(auth_api_client_factory):
    DummyAuthApiService.me_response = make_user()

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/request-password-reset", json=build_password_reset_request())

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    assert DummyDelay.calls == ["user@example.com"]


@pytest.mark.asyncio
async def test_password_reset_request_returns_500_when_user_lookup_fails(auth_api_client_factory):
    DummyAuthApiService.raise_on_me = RuntimeError("lookup failed")

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/request-password-reset", json=build_password_reset_request())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_password_reset_request_returns_404_when_user_missing(auth_api_client_factory):
    DummyAuthApiService.me_response = None

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/request-password-reset", json=build_password_reset_request())

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_password_reset_request_returns_500_when_email_enqueue_fails(
    auth_api_client_factory,
    monkeypatch,
):
    DummyAuthApiService.me_response = make_user()

    def raise_delay(email):
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(auth_api_module.send_email_to_recover_password, "delay", raise_delay)

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/request-password-reset", json=build_password_reset_request())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_password_reset_request_returns_422_for_invalid_email(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/request-password-reset", json={"email": "bad-email"})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_password_reset_request_returns_422_for_empty_body(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/request-password-reset", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_password_change_returns_ok(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/password-reset", json=build_password_change_payload())

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    assert DummyAuthApiService.last_change_password.token == "reset-token"


@pytest.mark.asyncio
async def test_password_change_returns_500_for_unexpected_service_error(auth_api_client_factory):
    DummyAuthApiService.raise_on_change_password = RuntimeError("unexpected reset error")

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/password-reset", json=build_password_change_payload())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_password_change_maps_incorrect_token(auth_api_client_factory):
    DummyAuthApiService.raise_on_change_password = IncorrectTokenException()

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/password-reset", json=build_password_change_payload())

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_password_change_maps_password_mismatch(auth_api_client_factory):
    DummyAuthApiService.raise_on_change_password = PasswordDoNotMatchException()

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/password-reset", json=build_password_change_payload())

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_field", ["token", "password", "confirm_new_password"])
async def test_password_change_returns_422_when_required_field_missing(auth_api_client_factory, missing_field):
    payload = build_password_change_payload()
    payload.pop(missing_field)

    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/password-reset", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_password_change_returns_422_for_empty_body(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.post("/auth/password-reset", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_returns_ok(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.patch("/auth/update", json=build_update_user_payload())

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
    assert DummyAuthApiService.last_update_args[0] == USER_ID
    assert DummyAuthApiService.last_update_args[1].username == "updated-name"


@pytest.mark.asyncio
async def test_update_user_maps_not_found(auth_api_client_factory):
    DummyAuthApiService.raise_on_update = ObjectNotFoundException()

    async for client, _ in auth_api_client_factory():
        response = await client.patch("/auth/update", json=build_update_user_payload())

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_maps_several_objects(auth_api_client_factory):
    DummyAuthApiService.raise_on_update = SeveralObjectsFoundException()

    async for client, _ in auth_api_client_factory():
        response = await client.patch("/auth/update", json=build_update_user_payload())

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_user_maps_incorrect_token(auth_api_client_factory):
    DummyAuthApiService.raise_on_update = IncorrectTokenException()

    async for client, _ in auth_api_client_factory():
        response = await client.patch("/auth/update", json=build_update_user_payload())

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_returns_500_for_custom_app_exception(auth_api_client_factory):
    DummyAuthApiService.raise_on_update = MyAppException()

    async for client, _ in auth_api_client_factory():
        response = await client.patch("/auth/update", json=build_update_user_payload())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_update_user_returns_500_for_unexpected_service_error(auth_api_client_factory):
    DummyAuthApiService.raise_on_update = RuntimeError("unexpected update error")

    async for client, _ in auth_api_client_factory():
        response = await client.patch("/auth/update", json=build_update_user_payload())

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_update_user_accepts_empty_payload_and_returns_ok(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.patch("/auth/update", json={})

    assert response.status_code == 200
    assert DummyAuthApiService.last_update_args[1].model_dump(exclude_unset=True) == {}


@pytest.mark.asyncio
async def test_update_user_returns_422_for_invalid_birth_date(auth_api_client_factory):
    payload = build_update_user_payload(birth_date="bad-date")

    async for client, _ in auth_api_client_factory():
        response = await client.patch("/auth/update", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_returns_422_for_invalid_boolean(auth_api_client_factory):
    payload = build_update_user_payload(online="not-bool")

    async for client, _ in auth_api_client_factory():
        response = await client.patch("/auth/update", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_burnout_calculate_uses_current_user_when_target_missing(auth_api_client_factory):
    DummyTestService.response = [build_test_result("2026-04-10T10:00:00", [1, 2, 3, 4, 5])]

    async for client, _ in auth_api_client_factory():
        response = await client.get("/auth/burnout_calculate")

    assert response.status_code == 200
    assert response.json() == {"result": 0.42}
    assert DummyTestService.last_args == ("e89f7acb-cd31-4d27-aadd-24f6c7d52794", USER_ID)
    assert DummyAuthApiService.last_burnout_input == DummyTestService.response


@pytest.mark.asyncio
async def test_burnout_calculate_accepts_explicit_user_id(auth_api_client_factory):
    DummyTestService.response = [build_test_result("2026-04-10T10:00:00", [1, 2, 3, 4, 5])]

    async for client, _ in auth_api_client_factory():
        response = await client.get(f"/auth/burnout_calculate?user_id={SECOND_USER_ID}")

    assert response.status_code == 200
    assert DummyTestService.last_args == ("e89f7acb-cd31-4d27-aadd-24f6c7d52794", SECOND_USER_ID)


@pytest.mark.asyncio
async def test_burnout_calculate_returns_404_for_not_found_condition(auth_api_client_factory):
    DummyTestService.raise_on_get = ObjectNotFoundException()

    async for client, _ in auth_api_client_factory():
        response = await client.get("/auth/burnout_calculate")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_burnout_calculate_returns_500_when_calculation_fails(auth_api_client_factory):
    DummyTestService.response = [build_test_result("2026-04-10T10:00:00", [1, 2, 3, 4, 5])]
    DummyAuthApiService.raise_on_burnout = RuntimeError("calculation failed")

    async for client, _ in auth_api_client_factory():
        response = await client.get("/auth/burnout_calculate")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_burnout_calculate_maps_unexpected_error_to_500(auth_api_client_factory):
    DummyTestService.raise_on_get = RuntimeError("boom")

    async for client, _ in auth_api_client_factory():
        response = await client.get("/auth/burnout_calculate")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_burnout_calculate_returns_422_for_invalid_user_id(auth_api_client_factory):
    async for client, _ in auth_api_client_factory():
        response = await client.get("/auth/burnout_calculate?user_id=bad-uuid")

    assert response.status_code == 422
