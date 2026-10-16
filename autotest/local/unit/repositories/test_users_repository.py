from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from autotest.factories.auth import USER_ID, make_user
from src.repositories.users import UsersRepository
from src.schemas.users import UserRequestLogIn
from src.services.auth import AuthService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "missing_fields",
    [(), ("birth_date",), ("city",), ("birth_date", "city", "phone_number")],
)
async def test_login_reads_user_with_nullable_profile_fields(missing_fields):
    service = AuthService()
    password = "StrongPass123"
    user = make_user(hashed_password=service.hash_password(password))
    for field in missing_fields:
        setattr(user, field, None)

    result = Mock()
    result.scalars.return_value.first.return_value = user
    session = SimpleNamespace(execute=AsyncMock(return_value=result))
    service.db = SimpleNamespace(users=UsersRepository(session))

    access_token, refresh_token = await service.login_user(
        UserRequestLogIn(email=user.email, password=password)
    )

    assert service.decode_token(access_token)["user_id"] == str(USER_ID)
    assert service.decode_token(refresh_token, is_refresh=True)["user_id"] == str(USER_ID)
