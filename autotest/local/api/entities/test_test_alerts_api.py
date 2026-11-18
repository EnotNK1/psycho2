import datetime
import json
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.api.dependencies.db import get_db
from src.api.psychologist import router
from src.models.clients import ClientsOrm
from src.models.tests import (
    BordersOrm, ScaleOrm, ScaleResultOrm, TestOrm as QuestionnaireOrm,
    TestResultOrm as QuestionnaireResultOrm,
)
from src.models.users import UsersOrm
from src.repositories.test_result import TestResultRepository as ResultRepository
from src.repositories.clients import ClientsRepository
from src.repositories.users import UsersRepository
from src.services.auth import AuthService
from src.services.test_alerts import (
    BECK_TEST_ID, BECK_TOTAL_SCALE_ID, DASS_TEST_ID, STAI_TEST_ID,
)


@pytest.fixture
def alerts_db():
    engine = create_engine("sqlite:///:memory:")
    for model in (
        UsersOrm, ClientsOrm, QuestionnaireOrm, ScaleOrm, BordersOrm,
        QuestionnaireResultOrm, ScaleResultOrm,
    ):
        model.__table__.create(engine)
    session = Session(engine, expire_on_commit=False)
    psychologist, other_psychologist, client, other_client = [uuid.uuid4() for _ in range(4)]
    for index, user_id in enumerate((psychologist, other_psychologist, client, other_client)):
        session.add(UsersOrm(
            id=user_id, username=f"User {index}", email=f"user{index}@example.com",
            hashed_password="unused", gender="string", role_id=2 if index < 2 else 1,
        ))
    session.add(ClientsOrm(
        id=uuid.uuid4(), client_id=client, mentor_id=psychologist,
        text="Confirmed", status=True,
    ))
    session.add(ClientsOrm(
        id=uuid.uuid4(), client_id=other_client, mentor_id=other_psychologist,
        text="Other psychologist", status=True,
    ))
    ids = {str(BECK_TEST_ID), str(DASS_TEST_ID), str(STAI_TEST_ID)}
    tests = json.loads(Path("src/services/info/test_info.json").read_text(encoding="utf-8"))
    scales = json.loads(Path("src/services/info/scale_info.json").read_text(encoding="utf-8"))
    borders = json.loads(Path("src/services/info/borders_info.json").read_text(encoding="utf-8"))
    scale_ids = set()
    scales_by_test = {}
    for item in tests:
        if item["id"] in ids:
            session.add(QuestionnaireOrm(**{**item, "id": uuid.UUID(item["id"])}))
    for item in scales:
        if item["test_id"] in ids:
            scale_id = uuid.UUID(item["id"])
            test_id = uuid.UUID(item["test_id"])
            scale_ids.add(item["id"])
            scales_by_test.setdefault(test_id, []).append(scale_id)
            session.add(ScaleOrm(
                id=scale_id, test_id=test_id, title=item["title"],
                min=item["min"], max=item["max"],
            ))
    for item in borders:
        if item["scale_id"] in scale_ids:
            session.add(BordersOrm(**{
                **item, "id": uuid.UUID(item["id"]), "scale_id": uuid.UUID(item["scale_id"]),
            }))
    session.commit()

    statements = []

    async def execute(statement):
        statements.append(statement)
        return session.execute(statement)

    adapter = SimpleNamespace(execute=execute)
    db = SimpleNamespace(
        users=UsersRepository(adapter), test_result=ResultRepository(adapter),
        clients=ClientsRepository(adapter),
    )

    def add_result(test_id, scores, owner=None, date=None):
        result_id = uuid.uuid4()
        session.add(QuestionnaireResultOrm(
            id=result_id, user_id=owner or client, test_id=test_id,
            date=date or datetime.datetime(2026, 10, 25, 12),
        ))
        for scale_id, score in scores.items():
            session.add(ScaleResultOrm(
                id=uuid.uuid4(), scale_id=scale_id, score=score, test_result_id=result_id,
            ))
        session.commit()
        return result_id

    app = FastAPI()
    app.include_router(router)

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    async def get_as(user_id=psychologist, token_role=2, path="/psychologist/alerts"):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver",
        ) as http:
            if user_id is not None:
                token, _ = AuthService().create_tokens({
                    "user_id": str(user_id), "role_id": token_role,
                })
                http.cookies.set("access_token", token)
            return await http.get(path)

    try:
        yield SimpleNamespace(
            session=session, psychologist=psychologist, other_psychologist=other_psychologist,
            client=client, other_client=other_client, scales=scales_by_test,
            add_result=add_result, get_as=get_as, statements=statements,
        )
    finally:
        session.close()
        engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("score,expected", [(29, False), (30, True), (63, True), (64, False)])
async def test_beck_uses_only_inclusive_total_threshold(alerts_db, score, expected):
    result_id = alerts_db.add_result(BECK_TEST_ID, {BECK_TOTAL_SCALE_ID: score})
    response = await alerts_db.get_as()
    assert response.status_code == 200
    assert [item["test_result_id"] for item in response.json()] == (
        [str(result_id)] if expected else []
    )


@pytest.mark.asyncio
async def test_beck_high_subscales_do_not_trigger_alert(alerts_db):
    subs = alerts_db.scales[BECK_TEST_ID][1:]
    alerts_db.add_result(BECK_TEST_ID, {subs[0]: 39, subs[1]: 24})
    assert (await alerts_db.get_as()).json() == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_id,index,threshold,maximum",
    [
        (DASS_TEST_ID, 0, 11, 28), (DASS_TEST_ID, 1, 8, 28),
        (DASS_TEST_ID, 2, 9, 28), (STAI_TEST_ID, 0, 45, 80),
        (STAI_TEST_ID, 1, 45, 80),
    ],
)
@pytest.mark.parametrize("position", ["below", "at", "max", "above"])
async def test_any_high_scale_uses_matching_category(
    alerts_db, test_id, index, threshold, maximum, position
):
    score = {"below": threshold - 1, "at": threshold, "max": maximum, "above": maximum + 1}[position]
    alerts_db.add_result(test_id, {alerts_db.scales[test_id][index]: score})
    response = await alerts_db.get_as()
    assert response.status_code == 200
    assert len(response.json()) == (1 if position in ("at", "max") else 0)


@pytest.mark.asyncio
async def test_multiple_high_scales_and_duplicate_relations_return_one_alert(alerts_db):
    result_id = alerts_db.add_result(DASS_TEST_ID, {
        scale_id: 21 for scale_id in alerts_db.scales[DASS_TEST_ID]
    })
    alerts_db.session.add(ClientsOrm(
        id=uuid.uuid4(), client_id=alerts_db.client, mentor_id=alerts_db.psychologist,
        text="Duplicate relation", status=True,
    ))
    alerts_db.session.commit()
    response = await alerts_db.get_as()
    assert response.status_code == 200
    assert response.json() == [{
        "client_id": str(alerts_db.client), "client_name": "User 2",
        "test_id": str(DASS_TEST_ID), "test_title": "Почему я себя так чувствую?",
        "test_result_id": str(result_id), "date": "2026-10-25T12:00:00",
    }]
    assert len(alerts_db.statements) == 2


@pytest.mark.asyncio
async def test_other_clients_and_pending_relations_are_hidden(alerts_db):
    alerts_db.add_result(BECK_TEST_ID, {BECK_TOTAL_SCALE_ID: 63}, owner=alerts_db.other_client)
    alerts_db.session.add(ClientsOrm(
        id=uuid.uuid4(), client_id=alerts_db.other_client, mentor_id=alerts_db.psychologist,
        text="Pending", status=False,
    ))
    alerts_db.session.commit()
    assert (await alerts_db.get_as()).json() == []
    assert len((await alerts_db.get_as(alerts_db.other_psychologist)).json()) == 1


@pytest.mark.asyncio
async def test_revoked_relation_hides_existing_alert(alerts_db):
    alerts_db.add_result(BECK_TEST_ID, {BECK_TOTAL_SCALE_ID: 63})
    assert len((await alerts_db.get_as()).json()) == 1
    relation = alerts_db.session.query(ClientsOrm).filter_by(client_id=alerts_db.client).one()
    relation.status = False
    alerts_db.session.commit()
    assert (await alerts_db.get_as()).json() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [0, 1, 3, 4])
async def test_non_psychologists_cannot_read_alerts_even_with_stale_role_token(alerts_db, role):
    user = alerts_db.session.get(UsersOrm, alerts_db.psychologist)
    user.role_id = role
    alerts_db.session.commit()
    assert (await alerts_db.get_as(token_role=2)).status_code == 403


@pytest.mark.asyncio
async def test_anonymous_user_cannot_read_alerts(alerts_db):
    assert (await alerts_db.get_as(None)).status_code == 401


@pytest.mark.asyncio
async def test_empty_plan_and_missing_psychologist(alerts_db):
    assert (await alerts_db.get_as()).json() == []
    assert (await alerts_db.get_as(uuid.uuid4())).status_code == 403


@pytest.mark.asyncio
async def test_each_high_attempt_remains_an_alert_newest_first(alerts_db):
    old = alerts_db.add_result(
        BECK_TEST_ID, {BECK_TOTAL_SCALE_ID: 30}, date=datetime.datetime(2026, 10, 20),
    )
    new = alerts_db.add_result(BECK_TEST_ID, {BECK_TOTAL_SCALE_ID: 63})
    alerts_db.add_result(
        BECK_TEST_ID, {BECK_TOTAL_SCALE_ID: 5}, date=datetime.datetime(2026, 10, 26),
    )
    assert [item["test_result_id"] for item in (await alerts_db.get_as()).json()] == [str(new), str(old)]


@pytest.mark.asyncio
async def test_encrypted_and_legacy_plaintext_scores_are_supported(alerts_db):
    alerts_db.add_result(BECK_TEST_ID, {BECK_TOTAL_SCALE_ID: 63})
    raw = alerts_db.session.execute(text("SELECT score FROM scale_result")).scalar_one()
    assert raw.startswith("enc::")
    assert len((await alerts_db.get_as()).json()) == 1
    alerts_db.session.execute(text("UPDATE scale_result SET score='30'"))
    alerts_db.session.commit()
    assert len((await alerts_db.get_as()).json()) == 1


@pytest.mark.asyncio
async def test_category_rules_come_from_current_borders_not_color(alerts_db):
    alerts_db.add_result(STAI_TEST_ID, {alerts_db.scales[STAI_TEST_ID][0]: 45})
    border = alerts_db.session.query(BordersOrm).filter_by(
        scale_id=alerts_db.scales[STAI_TEST_ID][0], title="Выше нормы",
    ).one()
    border.left_border = 50
    alerts_db.session.commit()
    assert (await alerts_db.get_as()).json() == []
    border.left_border = 45
    border.color = "#015641"
    alerts_db.session.commit()
    assert len((await alerts_db.get_as()).json()) == 1


@pytest.mark.asyncio
async def test_unrelated_tests_do_not_trigger_alerts(alerts_db):
    other_test, other_scale = uuid.uuid4(), uuid.uuid4()
    alerts_db.session.add(QuestionnaireOrm(
        id=other_test, title="Unrelated", description="", short_desc="", link="",
    ))
    alerts_db.session.add(ScaleOrm(
        id=other_scale, test_id=other_test, title="Other scale", min=0, max=100,
    ))
    alerts_db.session.add(BordersOrm(
        id=uuid.uuid4(), scale_id=other_scale, left_border=0, right_border=100,
        title="Высокий", color="#C52746",
    ))
    alerts_db.session.commit()
    alerts_db.add_result(other_test, {other_scale: 100})
    assert (await alerts_db.get_as()).json() == []


@pytest.mark.asyncio
async def test_scale_must_belong_to_the_result_test(alerts_db):
    alerts_db.add_result(STAI_TEST_ID, {alerts_db.scales[DASS_TEST_ID][0]: 21})
    assert (await alerts_db.get_as()).json() == []


@pytest.mark.asyncio
async def test_alert_reading_does_not_mark_or_remove_alerts(alerts_db):
    alerts_db.add_result(BECK_TEST_ID, {BECK_TOTAL_SCALE_ID: 30})
    first = await alerts_db.get_as()
    second = await alerts_db.get_as()
    assert first.json() == second.json()
    assert alerts_db.session.query(QuestionnaireResultOrm).count() == 1


@pytest.mark.asyncio
async def test_psychologist_without_clients_gets_empty_list(alerts_db):
    alerts_db.add_result(BECK_TEST_ID, {BECK_TOTAL_SCALE_ID: 63})
    assert (await alerts_db.get_as(alerts_db.other_psychologist)).json() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_client", [False, True])
async def test_client_test_history_returns_404_for_unrelated_client(alerts_db, missing_client):
    client_id = uuid.uuid4() if missing_client else alerts_db.other_client
    response = await alerts_db.get_as(
        path=f"/psychologist/clients/{client_id}/test-results"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_confirmed_client_without_results_returns_empty_history(alerts_db):
    response = await alerts_db.get_as(
        path=f"/psychologist/clients/{alerts_db.client}/test-results"
    )
    assert response.status_code == 200
    assert response.json() == []
