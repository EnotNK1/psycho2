import pytest
import datetime


@pytest.mark.parametrize(
    "email, username, birth_date, gender, city, phone_number, password, confirm_password, status_code",
    [
        (
            "Maksim4ik@email.com",
            "Maksim",
            "2025-02-22",
            "male",
            "Tomsk",
            "phone:)",
            "1234",
            "1234",
            200,
        ),
        (
            "Maksim4ik@email.com",
            "Maksim",
            "2025-02-22",
            "male",
            "Tomsk",
            "phone:)",
            "1234",
            "1234",
            409,
        ),
        (
            "Maksim4ik@email.com",
            "Maksim",
            "2025-02-22",
            "male",
            "Tomsk",
            "phone:)",
            "1234",
            "123",
            401,
        ),
        (
            "Maksim4ik@email.com",
            "Maksim",
            "20",
            "male",
            "Tomsk",
            "phone:)",
            "1234",
            "1234",
            422,
        ),
        (
            "Maksim4ik11@email.com",
            "Maksim",
            "2025-02-22",
            "male",
            "Tomsk",
            "phone:)",
            "1234",
            "1234",
            200,
        ),
        (
            "Maks",
            "Maksim",
            "2025-02-22",
            "male",
            "Tomsk",
            "phone:)",
            "1234",
            "1234",
            422,
        ),
        (
            "Maksim4ik@email",
            "Maksim",
            "2025-02-22",
            "male",
            "Tomsk",
            "phone:)",
            "1234",
            "1234",
            422,
        ),
    ],
)
async def test_auth_flow(
    email: str,
    username: str,
    birth_date: datetime.date,
    gender: str,
    city: str,
    phone_number: str,
    password: str,
    confirm_password: str,
    status_code: int,
    ac,
):
    # /register
    resp_register = await ac.post(
        "/auth/register",
        json={
            "email": email,
            "username": username,
            "birth_date": birth_date,
            "gender": gender,
            "city": city,
            "phone_number": phone_number,
            "password": password,
            "confirm_password": confirm_password,
        },
    )
    assert resp_register.status_code == status_code
    if status_code != 200:
        return
    # /login
    resp_login = await ac.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert resp_login.status_code == 200
    assert ac.cookies["access_token"]
    assert "access_token" in resp_login.json()
    # /me
    resp_me = await ac.get("/auth/me")
    assert resp_me.status_code == 200
    user = resp_me.json()
    assert user["email"] == email
    assert "id" in user
    assert "password" not in user
    assert "hashed_password" not in user
    # /logout
    resp_logout = await ac.post("/auth/logout")
    assert resp_logout.status_code == 200
    assert "access_token" not in ac.cookies
