import uuid

import pytest
import datetime


@pytest.mark.parametrize(
    "text, email, password, status_code",
    [
        (
            "first_review",
            "maksimka@yandex.ru",
            "1234",
            200,
        ),
        (
            32131,
            "maksimka@yandex.ru",
            "1234",
            422,
        ),
    ],
)
async def test_review_flow(
    text: str,
    email: str,
    password: str,
    status_code: int,
    ac,
):
    # /register
    data = {
        "email": email,
        "username": "string",
        "birth_date": "2025-02-22",
        "gender": "string",
        "city": "string",
        "phone_number": "string",
        "password": password,
        "confirm_password": password,
    }
    await ac.post(
        "/auth/register",
        json=data,
    )
    # /login
    await ac.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    # create
    resp_add = await ac.post(
        "/review",
        json={
            "text": text,
        },
    )
    assert resp_add.status_code == status_code
    if status_code != 200:
        return
    # read
    resp_read = await ac.get(
        "/review",
    )
    assert resp_read.status_code == 200
    review = resp_read.json()
    assert review[0]["text"] == text
    assert review[0]["is_read"] == False
    review_id = review[0]["id"]
    assert isinstance(review_id, str)

    # update
    await ac.patch(f"/review/{review_id}")

    resp_read = await ac.get(
        "/review",
    )
    assert resp_read.status_code == 200
    review = resp_read.json()
    assert review[0]["text"] == text
    assert review[0]["is_read"] == True

    # delete
    resp_del = await ac.delete(f"/review/{review_id}")
    assert resp_del.status_code == 200

    resp_read = await ac.get(
        "/review",
    )
    assert resp_read.status_code == 200
    review = resp_read.json()
    assert review == []
