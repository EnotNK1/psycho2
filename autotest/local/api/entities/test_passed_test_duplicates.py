import datetime
import uuid
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.api.dependencies.db import get_db
from src.api.psychologist import router as psychologist_router
from src.api.tests import router as questionnaire_router
from src.models.clients import ClientsOrm
from src.models.tests import (
    BordersOrm, ScaleOrm, ScaleResultOrm, TestOrm as QuestionnaireOrm,
    TestResultOrm as QuestionnaireResultOrm,
)
from src.models.users import UsersOrm
from src.repositories.borders import BordersRepository
from src.repositories.clients import ClientsRepository
from src.repositories.scale import ScalesRepository
from src.repositories.scale_result import ScaleResultRepository
from src.repositories.test_result import TestResultRepository as ResultRepository
from src.repositories.tests import TestsRepository as QuestionnaireRepository
from src.repositories.users import UsersRepository
from src.services.auth import AuthService


@pytest.fixture
def passed_tests_db():
    engine = create_engine("sqlite:///:memory:")
    for model in (
        UsersOrm, ClientsOrm, QuestionnaireOrm, ScaleOrm, BordersOrm,
        QuestionnaireResultOrm, ScaleResultOrm,
    ):
        model.__table__.create(engine)
    session = Session(engine, expire_on_commit=False)
    client_id, psychologist_id, other_client_id = [uuid.uuid4() for _ in range(3)]
    test_id, other_test_id = uuid.uuid4(), uuid.uuid4()
    for index, user_id in enumerate((client_id, psychologist_id, other_client_id)):
        session.add(UsersOrm(
            id=user_id, username=f"User {index}", email=f"user{index}@example.com",
            hashed_password="unused", gender="string", role_id=2 if index == 1 else 1,
        ))
    session.add(ClientsOrm(
        id=uuid.uuid4(), client_id=client_id, mentor_id=psychologist_id,
        status=True, text="Confirmed",
    ))
    scale_ids = {}
    for tid in (test_id, other_test_id):
        session.add(QuestionnaireOrm(
            id=tid, title="Same test name", description="Description", short_desc="Short",
            link="/images/test.png",
        ))
        sid = uuid.uuid4()
        scale_ids[tid] = sid
        session.add(ScaleOrm(id=sid, test_id=tid, title="Scale", min=0, max=100))
        session.add(BordersOrm(
            id=uuid.uuid4(), scale_id=sid, left_border=0, right_border=100,
            title="Category", color="#015641", user_recommendation="Recommendation",
        ))
    session.commit()

    def add_attempt(tid=test_id, user_id=client_id, day=25):
        rid = uuid.uuid4()
        session.add(QuestionnaireResultOrm(
            id=rid, user_id=user_id, test_id=tid, date=datetime.datetime(2026, 10, day, 12),
        ))
        session.add(ScaleResultOrm(
            id=uuid.uuid4(), test_result_id=rid, scale_id=scale_ids[tid], score=day,
        ))
        session.commit()
        return rid

    async def execute(statement):
        return session.execute(statement)

    adapter = SimpleNamespace(execute=execute)
    db = SimpleNamespace(
        users=UsersRepository(adapter), clients=ClientsRepository(adapter),
        tests=QuestionnaireRepository(adapter), test_result=ResultRepository(adapter),
        scales=ScalesRepository(adapter), scale_result=ScaleResultRepository(adapter),
        borders=BordersRepository(adapter),
    )
    app = FastAPI()
    app.include_router(questionnaire_router)
    app.include_router(psychologist_router)

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    async def get(path, as_psychologist=False):
        user_id = psychologist_id if as_psychologist else client_id
        token, _ = AuthService().create_tokens({
            "user_id": str(user_id), "role_id": 2 if as_psychologist else 1,
        })
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver",
        ) as http:
            http.cookies.set("access_token", token)
            return await http.get(path)

    try:
        yield SimpleNamespace(
            session=session, client_id=client_id, other_client_id=other_client_id,
            test_id=test_id, other_test_id=other_test_id, add_attempt=add_attempt, get=get,
        )
    finally:
        session.close()
        engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("by_user_id", [False, True])
async def test_second_attempt_does_not_create_another_card(passed_tests_db, by_user_id):
    db = passed_tests_db
    path = f"/tests/passed/user/{db.client_id}" if by_user_id else "/tests/passed/user"
    db.add_attempt()
    first = await db.get(path)
    assert first.status_code == 200
    assert len(first.json()) == 1
    db.add_attempt(day=26)
    second = await db.get(path)
    assert second.status_code == 200
    assert second.json() == first.json()
    assert db.session.query(QuestionnaireResultOrm).count() == 2
    assert db.session.query(ScaleResultOrm).count() == 2


@pytest.mark.asyncio
async def test_each_test_gets_its_own_card_even_with_the_same_title(passed_tests_db):
    db = passed_tests_db
    db.add_attempt()
    db.add_attempt(day=26)
    db.add_attempt(tid=db.other_test_id)
    response = await db.get(f"/tests/passed/user/{db.client_id}")
    assert response.status_code == 200
    assert {item["test_id"] for item in response.json()} == {
        str(db.test_id), str(db.other_test_id),
    }
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_another_clients_results_do_not_create_cards(passed_tests_db):
    db = passed_tests_db
    db.add_attempt(user_id=db.other_client_id)
    response = await db.get("/tests/passed/user")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_client_and_psychologist_histories_keep_all_attempts_and_dates(passed_tests_db):
    db = passed_tests_db
    first = db.add_attempt(day=25)
    second = db.add_attempt(day=26)
    for path, as_psychologist in (
        (f"/tests/{db.test_id}/results/", False),
        (f"/psychologist/clients/{db.client_id}/tests/{db.test_id}/results", True),
    ):
        response = await db.get(path, as_psychologist=as_psychologist)
        assert response.status_code == 200
        results = response.json()
        assert {item["test_result_id"] for item in results} == {str(first), str(second)}
        assert {item["datetime"] for item in results} == {
            "2026-10-25T12:00:00", "2026-10-26T12:00:00",
        }
        assert {item["scale_results"][0]["score"] for item in results} == {25, 26}


@pytest.mark.asyncio
async def test_psychologist_summary_keeps_one_card_with_latest_result(passed_tests_db):
    db = passed_tests_db
    db.add_attempt(day=25)
    latest = db.add_attempt(day=26)
    response = await db.get(
        f"/psychologist/clients/{db.client_id}/test-results", as_psychologist=True,
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["test_result_id"] == str(latest)
    assert response.json()[0]["last_date"] == "2026-10-26T12:00:00"
