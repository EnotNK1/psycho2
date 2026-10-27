import uuid
from sqlalchemy import select, func
from src.models import UsersOrm, ClientsOrm, ApplicationOrm, InquiryOrm
from src.services.auth import AuthService, serializer


def test_anonymous_and_fake_token(sandbox):
    sandbox.http.cookies.clear()
    for path in ["/auth/me", "/client", "/psychologist/alerts"]:
        assert sandbox.http.get(path).status_code == 401
    token, _ = AuthService().create_tokens({"user_id": str(uuid.uuid4()), "role_id": 2})
    sandbox.http.cookies.set("compas_access_token", token)
    assert sandbox.http.get("/psychologist/alerts").status_code == 401


def test_profile_cannot_promote_itself(sandbox):
    sandbox.login("user")
    response = sandbox.http.patch(
        "/psychologist/become",
        json={
            "username": "Profile",
            "birth_date": "1990-01-01",
            "higher_education_university": "University",
            "higher_education_specialization": "Psychology",
            "work_format": "online",
            "inquiry_ids": [],
        },
    )
    assert response.status_code == 200, response.text
    assert sandbox.http.get("/auth/me").json()["role_id"] == 1
    assert sandbox.http.get("/psychologist/alerts").status_code == 403


def test_delete_profile_cascades_own_links_only(sandbox):
    user = sandbox.session.get(UsersOrm, sandbox.ids["user"])
    inquiry = InquiryOrm(id=98765, text="Test")
    user.inquiries = [inquiry]
    sandbox.session.add(
        ClientsOrm(
            id=uuid.uuid4(),
            client_id=user.id,
            mentor_id=sandbox.ids["psychologist"],
            text="Accepted",
            status=True,
        )
    )
    sandbox.session.add(
        ApplicationOrm(
            client_id=user.id,
            manager_id=sandbox.ids["psychologist"],
            text="Application",
            inquiry=[],
            status=True,
        )
    )
    sandbox.session.commit()
    sandbox.login("user")
    assert sandbox.http.delete("/auth/delete").status_code == 200
    assert sandbox.session.scalar(select(func.count()).select_from(UsersOrm)) == 4
    assert sandbox.session.scalar(select(func.count()).select_from(ClientsOrm)) == 0
    assert sandbox.session.scalar(select(func.count()).select_from(ApplicationOrm)) == 0
    assert sandbox.http.get("/auth/me").status_code == 401


def test_password_reset_uses_independent_timed_secret(sandbox):
    token = serializer.dumps("user@example.com")
    response = sandbox.http.post(
        "/auth/password-reset",
        json={
            "token": token,
            "password": "DifferentPassword123!",
            "confirm_new_password": "DifferentPassword123!",
        },
    )
    assert response.status_code == 200, response.text
    response = sandbox.http.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "DifferentPassword123!"},
    )
    assert response.status_code == 200
    assert sandbox.http.post(
        "/auth/password-reset",
        json={
            "token": token + "tampered",
            "password": "DifferentPassword123!",
            "confirm_new_password": "DifferentPassword123!",
        },
    ).status_code in (400, 401)


def test_short_or_overlong_password_rejected(sandbox):
    for password in ["short", "x" * 73]:
        response = sandbox.http.post(
            "/auth/register",
            json={
                "email": "invalid@example.com",
                "username": "Bad",
                "gender": "male",
                "password": password,
                "confirm_password": password,
            },
        )
        assert response.status_code == 400, response.text
    assert sandbox.session.scalar(select(func.count()).select_from(UsersOrm)) == 5


def test_cookies_do_not_overwrite_original_project_login(sandbox):
    sandbox.http.cookies.set("access_token", "original-project-token")
    sandbox.login("user")
    sandbox.http.cookies.set("access_token", "original-project-token")
    assert sandbox.http.get("/auth/me").status_code == 200
    assert sandbox.http.post("/auth/logout").status_code == 200
    assert sandbox.http.cookies.get("access_token") == "original-project-token"
    assert sandbox.http.get("/auth/me").status_code == 401
