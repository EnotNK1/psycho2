import datetime
import uuid
from types import SimpleNamespace


USER_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
SECOND_USER_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")


def build_register_payload(
    *,
    email="user@example.com",
    username="tester",
    birth_date="1999-01-01",
    gender="male",
    city="Tomsk",
    phone_number="+70000000000",
    password="StrongPass123",
    confirm_password="StrongPass123",
):
    return {
        "email": email,
        "username": username,
        "birth_date": birth_date,
        "gender": gender,
        "city": city,
        "phone_number": phone_number,
        "password": password,
        "confirm_password": confirm_password,
    }


def build_login_payload(email="user@example.com", password="StrongPass123"):
    return {"email": email, "password": password}


def build_refresh_payload(refresh_token="refresh-token"):
    return {"refresh_token": refresh_token}


def build_password_reset_request(email="user@example.com"):
    return {"email": email}


def build_password_change_payload(
    *,
    token="reset-token",
    password="NewStrongPass123",
    confirm_new_password="NewStrongPass123",
):
    return {
        "token": token,
        "password": password,
        "confirm_new_password": confirm_new_password,
    }


def build_update_user_payload(**overrides):
    payload = {
        "username": "updated-name",
        "description": "updated description",
        "city": "Novosibirsk",
        "company": "OpenAI",
        "online": True,
        "gender": "female",
        "birth_date": "1998-05-03",
        "phone_number": "+79990001122",
    }
    payload.update(overrides)
    return payload


def make_user(
    *,
    user_id=USER_ID,
    email="user@example.com",
    username="tester",
    role_id=1,
    hashed_password="$2b$12$dummy",
):
    return SimpleNamespace(
        id=user_id,
        email=email,
        username=username,
        birth_date=datetime.date(1999, 1, 1),
        gender="male",
        city="Tomsk",
        phone_number="+70000000000",
        description="profile",
        company="OpenAI",
        online=True,
        is_active=True,
        department="R&D",
        face_to_face=False,
        role_id=role_id,
        hashed_password=hashed_password,
    )


def build_test_result(dt: str, scores: list[int]):
    return {
        "datetime": dt,
        "scale_results": [{"score": score} for score in scores],
    }
