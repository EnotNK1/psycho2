import uuid
from pathlib import Path

import pytest
from sqlalchemy import select, func
from src.models import TestResultOrm as Result, ScaleResultOrm, BordersOrm
from src.utils.data import load_data
from src.services.auth import AuthService


@pytest.mark.asyncio
async def test_catalog_is_complete_and_repeat_seed_preserves_edits(sandbox):
    assert (await sandbox.seed())["created"] > 0
    border = sandbox.session.scalars(select(BordersOrm)).first()
    border.user_recommendation = "Manual edit"
    sandbox.session.commit()
    assert (await sandbox.seed())["created"] == 0
    assert (
        sandbox.session.get(BordersOrm, border.id).user_recommendation == "Manual edit"
    )
    tests = sandbox.http.get("/tests")
    assert tests.status_code == 200
    assert len(tests.json()) == len(load_data("src/services/info/test_info.json")) == 13
    for item in tests.json():
        detail = sandbox.http.get("/tests/" + item["id"])
        assert detail.status_code == 200, detail.text
        questions = sandbox.http.get(f"/tests/{item['id']}/questions/answers")
        assert questions.status_code == 200, questions.text
        assert all(q["answer_choices"] for q in questions.json())
        assert [q["number"] for q in questions.json()] == sorted(
            q["number"] for q in questions.json()
        )


@pytest.mark.asyncio
async def test_all_test_algorithms_and_repeat_history(sandbox):
    await sandbox.seed()
    sandbox.login("user")
    for item in sandbox.http.get("/tests").json():
        questions = sandbox.http.get(f"/tests/{item['id']}/questions/answers").json()
        payload = {
            "test_id": item["id"],
            "date": "2026-10-27T12:00:00",
            "results": [q["answer_choices"][0]["score"] for q in questions],
        }
        response = sandbox.http.post("/tests/result", json=payload)
        assert response.status_code == 200, (item["title"], response.text)
        result_id = response.json()["test_result_id"]
        assert sandbox.http.get(f"/tests/test_result/{result_id}").status_code == 200
        assert sandbox.http.post("/tests/result", json=payload).status_code == 200
        history = sandbox.http.get(f"/tests/{item['id']}/results/")
        assert history.status_code == 200, history.text
        assert len(history.json()) == 2
    assert len(sandbox.http.get("/tests/passed/user").json()) == 13
    assert sandbox.session.scalar(select(func.count()).select_from(Result)) == 26
    assert sandbox.session.scalar(select(func.count()).select_from(ScaleResultOrm)) > 26


@pytest.mark.asyncio
async def test_application_acceptance_alert_and_access_boundaries(sandbox):
    await sandbox.seed()
    sandbox.login("user")
    response = sandbox.http.post(
        "/applications",
        json={
            "manager_id": str(sandbox.ids["psychologist"]),
            "text": "Help",
            "inquiry": [],
        },
    )
    assert response.status_code == 200, response.text
    app_id = response.json()["app_id"]
    assert sandbox.http.patch(f"/applications/{app_id}/confirm").status_code == 404
    sandbox.login("other_psychologist")
    assert sandbox.http.get(f"/applications/{app_id}").status_code == 404
    assert sandbox.http.patch(f"/applications/{app_id}/confirm").status_code == 404
    sandbox.login("psychologist")
    assert sandbox.http.patch(f"/applications/{app_id}/confirm").status_code == 200
    assert len(sandbox.http.get("/client").json()) == 1
    sandbox.login("user")
    tid = "33d10952-aed7-4a4e-9e5a-dbd01b2f294d"
    questions = sandbox.http.get(f"/tests/{tid}/questions/answers").json()
    response = sandbox.http.post(
        "/tests/result",
        json={
            "test_id": tid,
            "date": "2026-10-27T12:00:00",
            "results": [
                max(a["score"] for a in q["answer_choices"]) for q in questions
            ],
        },
    )
    assert response.status_code == 200, response.text
    rid = response.json()["test_result_id"]
    sandbox.login("psychologist")
    alerts = sandbox.http.get("/psychologist/alerts")
    assert alerts.status_code == 200, alerts.text
    assert [a["test_result_id"] for a in alerts.json()] == [rid]
    assert sandbox.http.get(f"/tests/test_result/{rid}").status_code == 200
    sandbox.login("stranger")
    assert sandbox.http.get(f"/tests/test_result/{rid}").status_code == 404
    assert (
        sandbox.http.get(
            f"/tests/{tid}/results/?user_id={sandbox.ids['user']}"
        ).status_code
        == 404
    )
    assert (
        sandbox.http.get(f"/tests/passed/user/{sandbox.ids['user']}").status_code == 404
    )
    assert sandbox.http.get("/psychologist/alerts").status_code == 403
    assert sandbox.http.delete(f"/applications/{app_id}").status_code == 404
    sandbox.login("psychologist")
    assert sandbox.http.patch(f"/applications/{app_id}/confirm").status_code == 200
    assert sandbox.http.get("/psychologist/alerts").json() == []


@pytest.mark.asyncio
async def test_registration_profile_roles_and_invalid_answers(sandbox):
    await sandbox.seed()
    response = sandbox.http.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "username": "New",
            "gender": "female",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
        },
    )
    assert response.status_code == 200, response.text
    sandbox.http.post(
        "/auth/login", json={"email": "new@example.com", "password": "StrongPass123!"}
    )
    assert sandbox.http.get("/auth/me").json()["role_id"] == 1
    assert (
        sandbox.http.patch(
            "/auth/update", json={"username": "Updated", "role_id": 0}
        ).status_code
        == 200
    )
    me = sandbox.http.get("/auth/me").json()
    assert me["role_id"] == 1 and me["username"] == "Updated"
    assert sandbox.http.post("/tests/auto").status_code == 403
    assert sandbox.http.get("/client").status_code == 403
    tid = "33d10952-aed7-4a4e-9e5a-dbd01b2f294d"
    response = sandbox.http.post(
        "/tests/result",
        json={"test_id": tid, "date": "2026-10-27T12:00:00", "results": [99] * 21},
    )
    assert response.status_code == 400, response.text
    assert sandbox.session.scalar(select(func.count()).select_from(Result)) == 0
    response = sandbox.http.post(
        "/auth/refresh-token", json={"refresh_token": "invalid"}
    )
    assert response.status_code in (400, 401)


def test_standalone_routes_assets_and_liveness(sandbox):
    paths = sandbox.http.get("/openapi.json").json()["paths"]
    assert "/psychologist/alerts" in paths
    assert not any(
        x.startswith(
            (
                "/mood_tracker",
                "/diary",
                "/ontology",
                "/education",
                "/exercises",
                "/chat-bot",
            )
        )
        for x in paths
    )
    assert sandbox.http.get("/health/live").status_code == 200
    assert sandbox.http.get("/images/../config.py").status_code == 404
    for test in load_data("src/services/info/test_info.json"):
        if test["link"].startswith("/images/"):
            assert sandbox.http.get(test["link"]).status_code == 200, test["link"]
    assert all(
        "psycho2"
        not in str(Path(module.__file__).resolve().relative_to(Path.cwd())).lower()
        for name, module in __import__("sys").modules.items()
        if name.startswith("src.") and getattr(module, "__file__", None)
    )


def test_ciphertext_and_token_separation(sandbox):
    from src.utils.encryption import encrypt_for_storage, decrypt_from_storage

    encrypted = encrypt_for_storage(42.0)
    assert encrypted.startswith("enc::") and encrypted != "42.0"
    assert decrypt_from_storage(encrypted, float) == 42.0
    access, refresh = AuthService().create_tokens(
        {"user_id": str(uuid.uuid4()), "role_id": 1}
    )
    assert AuthService().decode_token(access)["role_id"] == 1
    with pytest.raises(Exception):
        AuthService().decode_token(refresh)
