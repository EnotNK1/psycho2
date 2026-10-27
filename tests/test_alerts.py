from datetime import datetime
import uuid
import pytest
from sqlalchemy import select
from src.models import (
    ClientsOrm,
    TestResultOrm as Result,
    ScaleResultOrm,
    ScaleOrm,
    UsersOrm,
)
from src.services.test_alerts import (
    BECK_TEST_ID,
    BECK_TOTAL_SCALE_ID,
    DASS_TEST_ID,
    STAI_TEST_ID,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("score,expected", [(29, 0), (30, 1), (63, 1), (64, 0)])
async def test_beck_boundaries(sandbox, score, expected):
    await sandbox.seed()
    sandbox.session.add(
        ClientsOrm(
            id=uuid.uuid4(),
            client_id=sandbox.ids["user"],
            mentor_id=sandbox.ids["psychologist"],
            text="ok",
            status=True,
        )
    )
    result = Result(
        id=uuid.uuid4(),
        user_id=sandbox.ids["user"],
        test_id=BECK_TEST_ID,
        date=datetime(2026, 10, 27),
    )
    sandbox.session.add(result)
    sandbox.session.flush()
    sandbox.session.add(
        ScaleResultOrm(
            id=uuid.uuid4(),
            test_result_id=result.id,
            scale_id=BECK_TOTAL_SCALE_ID,
            score=score,
        )
    )
    sandbox.session.commit()
    sandbox.login("psychologist")
    response = sandbox.http.get("/psychologist/alerts")
    assert response.status_code == 200
    assert len(response.json()) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_id,position,threshold,maximum",
    [
        (DASS_TEST_ID, 1, 11, 28),
        (DASS_TEST_ID, 2, 8, 28),
        (DASS_TEST_ID, 3, 9, 28),
        (STAI_TEST_ID, 1, 45, 80),
        (STAI_TEST_ID, 2, 45, 80),
    ],
)
@pytest.mark.parametrize("boundary", ["below", "at", "maximum", "above"])
async def test_any_upper_scale(
    sandbox, test_id, position, threshold, maximum, boundary
):
    await sandbox.seed()
    sandbox.session.add(
        ClientsOrm(
            id=uuid.uuid4(),
            client_id=sandbox.ids["user"],
            mentor_id=sandbox.ids["psychologist"],
            text="ok",
            status=True,
        )
    )
    result = Result(
        id=uuid.uuid4(),
        user_id=sandbox.ids["user"],
        test_id=test_id,
        date=datetime(2026, 10, 27),
    )
    sandbox.session.add(result)
    sandbox.session.flush()
    scale = sandbox.session.scalar(
        select(ScaleOrm).where(
            ScaleOrm.test_id == test_id, ScaleOrm.position == position
        )
    )
    score = {
        "below": threshold - 1,
        "at": threshold,
        "maximum": maximum,
        "above": maximum + 1,
    }[boundary]
    sandbox.session.add(
        ScaleResultOrm(
            id=uuid.uuid4(), test_result_id=result.id, scale_id=scale.id, score=score
        )
    )
    sandbox.session.commit()
    sandbox.login("psychologist")
    response = sandbox.http.get("/psychologist/alerts")
    assert response.status_code == 200
    assert len(response.json()) == (1 if boundary in ("at", "maximum") else 0)


@pytest.mark.asyncio
async def test_multiple_high_scales_one_alert_and_old_token_cannot_grant_role(sandbox):
    await sandbox.seed()
    sandbox.session.add(
        ClientsOrm(
            id=uuid.uuid4(),
            client_id=sandbox.ids["user"],
            mentor_id=sandbox.ids["psychologist"],
            text="ok",
            status=True,
        )
    )
    result = Result(
        id=uuid.uuid4(),
        user_id=sandbox.ids["user"],
        test_id=DASS_TEST_ID,
        date=datetime(2026, 10, 27),
    )
    sandbox.session.add(result)
    sandbox.session.flush()
    for scale in sandbox.session.scalars(
        select(ScaleOrm).where(ScaleOrm.test_id == DASS_TEST_ID)
    ):
        sandbox.session.add(
            ScaleResultOrm(
                id=uuid.uuid4(), test_result_id=result.id, scale_id=scale.id, score=21
            )
        )
    sandbox.session.commit()
    sandbox.login("psychologist")
    assert len(sandbox.http.get("/psychologist/alerts").json()) == 1
    user = sandbox.session.get(UsersOrm, sandbox.ids["psychologist"])
    user.role_id = 1
    sandbox.session.commit()
    assert sandbox.http.get("/psychologist/alerts").status_code == 403
