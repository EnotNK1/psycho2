from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from itsdangerous import URLSafeTimedSerializer
from itsdangerous.timed import TimestampSigner
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.api.application import router as application_router
from src.api.dependencies.db import get_db
from src.api.diary import router as diary_router
from src.api.tests import router as results_router
from src.api.user_task import router as task_router
from src.enums import DailyTaskType
from src.exceptions import (
    IncorrectTokenException,
    MyAppException,
    ObjectNotFoundException,
)
from src.models.daily_tasks import DailyTaskOrm
from src.models.diary import DiaryOrm
from src.models.exercise import CompletedExerciseOrm, ExerciseStructureOrm
from src.models.inquiry import InquiryOrm
from src.models.user_inquiry import user_inquiry
from src.models.user_task import UserTaskOrm
from src.models.users import UsersOrm
from src.repositories.daily_tasks import DailyTasksRepository
from src.repositories.diary import DiaryRepository
from src.repositories.exercise import ExerciseRepository
from src.repositories.users import UsersRepository
from src.repositories.user_task import UserTaskRepository
from src.schemas.application import Application
from src.schemas.users import PasswordChangeRequest
from src.services.application import ApplicationService
from src.services.auth import AuthService, serializer
from src.services.daily_tasks import DailyTaskService
from src.services.psychologist import PsychologistService
from src.services.statistics import StatisticsService
from src.services.tests import TestService as ResultsService


@pytest.fixture
def memory_db():
    engine = create_engine("sqlite:///:memory:")
    for model in (
        UsersOrm,
        InquiryOrm,
        UserTaskOrm,
        DiaryOrm,
        DailyTaskOrm,
        ExerciseStructureOrm,
        CompletedExerciseOrm,
    ):
        model.__table__.create(engine)
    user_inquiry.create(engine)
    session = Session(engine, expire_on_commit=False)

    async def execute(statement):
        return session.execute(statement)

    async def commit():
        session.commit()

    async def rollback():
        session.rollback()

    adapter = SimpleNamespace(
        execute=execute,
        commit=commit,
        rollback=rollback,
        add=session.add,
        expire_all=session.expire_all,
    )
    db = SimpleNamespace(
        session=adapter,
        commit=commit,
        rollback=rollback,
        users=UsersRepository(adapter),
        diary=DiaryRepository(adapter),
        daily_tasks=DailyTasksRepository(adapter),
        exercise=ExerciseRepository(adapter),
    )
    try:
        yield db, session
    finally:
        session.close()
        engine.dispose()


def make_app(db, *routers):
    app = FastAPI()
    for router in routers:
        app.include_router(router)

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    return app


def login_cookie(user_id):
    access, _ = AuthService().create_tokens({"user_id": str(user_id), "role_id": 1})
    return {"access_token": access}


@pytest.mark.asyncio
@pytest.mark.parametrize("token_kind", ["valid", "old_key", "expired", "tampered"])
async def test_password_reset_rejects_unsafe_tokens(token_kind, monkeypatch):
    email = "audit@example.com"
    if token_kind == "old_key":
        token = URLSafeTimedSerializer("secret_key").dumps(email)
    elif token_kind == "expired":
        original = TimestampSigner.get_timestamp
        with patch.object(
            TimestampSigner, "get_timestamp", lambda self: original(self) - 7200
        ):
            token = serializer.dumps(email)
    else:
        token = serializer.dumps(email)
        if token_kind == "tampered":
            token = "invalid." + token
    db = SimpleNamespace(users=SimpleNamespace(edit=AsyncMock()), commit=AsyncMock())
    service = AuthService(db)
    monkeypatch.setattr(service, "hash_password", lambda _: "new-password-hash")
    request = PasswordChangeRequest(
        token=token, password="NewPass123", confirm_new_password="NewPass123"
    )

    if token_kind == "valid":
        await service.change_password(request)
        assert db.users.edit.await_args.kwargs["email"] == email
        db.commit.assert_awaited_once()
    else:
        with pytest.raises(IncorrectTokenException):
            await service.change_password(request)
        db.users.edit.assert_not_awaited()
        db.commit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("actor", ["anonymous", "other", "owner"])
@pytest.mark.parametrize("method", ["PATCH", "DELETE"])
async def test_task_mutations_require_owner(memory_db, actor, method):
    db, session = memory_db
    db.user_task = UserTaskRepository(db.session)
    owner = uuid4()
    task = UserTaskOrm(
        id=uuid4(),
        user_id=owner,
        text="original",
        created_at=datetime.now(),
        is_complete=False,
    )
    session.add(task)
    session.commit()
    cookies = (
        {}
        if actor == "anonymous"
        else login_cookie(owner if actor == "owner" else uuid4())
    )
    app = make_app(db, task_router)
    payload = {"user_task_id": str(task.id)}
    if method == "PATCH":
        payload["text"] = "changed"
    path = "/user-task/update" if method == "PATCH" else "/user-task"
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", cookies=cookies
    ) as client:
        response = await client.request(method, path, json=payload)
    assert response.status_code == {"anonymous": 401, "other": 404, "owner": 200}[actor]
    session.expire_all()
    stored = session.get(UserTaskOrm, task.id)
    if actor == "owner" and method == "DELETE":
        assert stored is None
    else:
        assert stored.text == ("changed" if actor == "owner" else "original")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role,related,allowed",
    [
        (1, False, False),
        (2, False, False),
        (2, True, True),
        (0, False, True),
        (3, True, False),
    ],
)
@pytest.mark.parametrize("endpoint", ["history", "passed", "detail"])
async def test_results_require_owner_admin_or_assigned_psychologist(
    role, related, allowed, endpoint
):
    actor, target, test_id, result_id = uuid4(), uuid4(), uuid4(), uuid4()
    db = SimpleNamespace(
        users=SimpleNamespace(
            get_one_or_none=AsyncMock(return_value=SimpleNamespace(role_id=role)),
            get_one=AsyncMock(return_value=SimpleNamespace(role_id=role)),
        ),
        clients=SimpleNamespace(
            get_one_or_none=AsyncMock(return_value=object() if related else None)
        ),
        test_result=SimpleNamespace(
            get_filtered=AsyncMock(return_value=[]),
            get_one=AsyncMock(
                return_value=SimpleNamespace(
                    id=result_id,
                    test_id=test_id,
                    user_id=target,
                    date=datetime.now(),
                )
            ),
        ),
        scale_result=SimpleNamespace(get_filtered=AsyncMock(return_value=[])),
    )
    app = make_app(db, results_router)
    path = {
        "history": f"/tests/{test_id}/results/?user_id={target}",
        "passed": f"/tests/passed/user/{target}",
        "detail": f"/tests/test_result/{result_id}",
    }[endpoint]
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=login_cookie(actor),
    ) as client:
        response = await client.get(path)
    assert response.status_code == (200 if allowed else 404)
    if allowed:
        if endpoint == "detail":
            db.scale_result.get_filtered.assert_awaited_once()
        else:
            db.test_result.get_filtered.assert_awaited_once()
        if role == 2:
            db.clients.get_one_or_none.assert_awaited_once_with(
                client_id=target, mentor_id=actor, status=True
            )
    else:
        db.test_result.get_filtered.assert_not_awaited()
        db.scale_result.get_filtered.assert_not_awaited()


@pytest.mark.asyncio
async def test_passed_tests_require_login():
    app = make_app(object(), results_router)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/tests/passed/user/{uuid4()}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_results_owner_does_not_need_client_relation():
    owner = uuid4()
    db = SimpleNamespace(
        users=SimpleNamespace(get_one_or_none=AsyncMock()),
        clients=SimpleNamespace(get_one_or_none=AsyncMock()),
    )
    await ResultsService(db).authorize_results_access(owner, owner)
    db.users.get_one_or_none.assert_not_awaited()
    db.clients.get_one_or_none.assert_not_awaited()


def application_db():
    application = Application(
        id=uuid4(),
        client_id=uuid4(),
        manager_id=uuid4(),
        status=False,
        text="private application",
        inquiry=[],
        created_at=datetime.now(),
    )
    db = SimpleNamespace(
        application=SimpleNamespace(
            get_filtered=AsyncMock(return_value=[application]),
            is_user_manager=AsyncMock(return_value=True),
            edit=AsyncMock(),
            delete=AsyncMock(),
        ),
        users=SimpleNamespace(
            get_one_or_none=AsyncMock(return_value=SimpleNamespace(role_id=1))
        ),
        clients=SimpleNamespace(
            get_one_or_none=AsyncMock(return_value=None), add=AsyncMock()
        ),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )
    return db, application


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["GET", "DELETE"])
@pytest.mark.parametrize(
    "actor", ["anonymous", "stranger", "sender", "recipient", "admin"]
)
async def test_application_read_and_delete_access(method, actor):
    db, application = application_db()
    actor_id = {
        "sender": application.client_id,
        "recipient": application.manager_id,
    }.get(actor, uuid4())
    if actor == "admin":
        db.users.get_one_or_none.return_value.role_id = 0
    cookies = {} if actor == "anonymous" else login_cookie(actor_id)
    async with AsyncClient(
        transport=ASGITransport(app=make_app(db, application_router)),
        base_url="http://test",
        cookies=cookies,
    ) as client:
        response = await client.request(method, f"/applications/{application.id}")
    expected = 401 if actor == "anonymous" else 404 if actor == "stranger" else 200
    assert response.status_code == expected
    if method == "DELETE" and expected == 200:
        db.application.delete.assert_awaited_once_with(id=application.id)
    else:
        db.application.delete.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("own_application", [False, True])
async def test_only_application_recipient_can_confirm(own_application):
    db, application = application_db()
    actor = application.manager_id if own_application else uuid4()
    service = ApplicationService(db)
    if own_application:
        await service.update_application_status(application.id, actor)
        relation = db.clients.add.await_args.args[0]
        assert relation.mentor_id == application.manager_id
        assert relation.client_id == application.client_id
    else:
        with pytest.raises(ObjectNotFoundException):
            await service.update_application_status(application.id, actor)
        assert application.status is False
        db.application.edit.assert_not_awaited()
        db.clients.add.assert_not_awaited()
        db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_multiple_tracker_notes_return_latest_without_losing_text(memory_db):
    db, session = memory_db
    owner, tracker = uuid4(), uuid4()
    now = datetime.now()
    session.add_all(
        [
            DiaryOrm(
                id=uuid4(),
                user_id=owner,
                mood_tracker_id=tracker,
                text="older",
                created_at=now - timedelta(hours=1),
            ),
            DiaryOrm(
                id=uuid4(),
                user_id=owner,
                mood_tracker_id=tracker,
                text="latest",
                created_at=now,
            ),
            DiaryOrm(
                id=uuid4(),
                user_id=uuid4(),
                mood_tracker_id=tracker,
                text="other user",
                created_at=now + timedelta(hours=1),
            ),
        ]
    )
    session.commit()
    async with AsyncClient(
        transport=ASGITransport(app=make_app(db, diary_router)),
        base_url="http://test",
        cookies=login_cookie(owner),
    ) as client:
        response = await client.get(f"/diary/by_mood_tracker/{tracker}")
        notes = await client.get("/diary")
        missing = await client.get(f"/diary/by_mood_tracker/{uuid4()}")
    assert response.status_code == 200
    assert response.json()["text"] == "latest"
    assert {note["text"] for note in notes.json()} == {"older", "latest"}
    assert missing.json() is None


@pytest.mark.asyncio
async def test_refresh_daily_tasks_persists_activity_and_does_not_duplicate(memory_db):
    db, session = memory_db
    owner, other = uuid4(), uuid4()
    for user_id in (owner, other):
        session.add(
            UsersOrm(
                id=user_id,
                username="tester",
                email=f"{user_id}@example.com",
                gender="male",
                role_id=1,
            )
        )
        session.add(
            DailyTaskOrm(
                id=uuid4(),
                user_id=user_id,
                title="unfinished",
                short_desc="description",
                destination_id=uuid4(),
                number=1,
                day=1,
                is_complete=False,
                is_current=False,
                type=DailyTaskType.THEORY,
            )
        )
    session.commit()
    service = DailyTaskService(db)
    await service.refresh_daily_tasks(owner)
    await service.refresh_daily_tasks(owner)
    session.expire_all()
    tasks = (
        session.execute(select(DailyTaskOrm).where(DailyTaskOrm.user_id == owner))
        .scalars()
        .all()
    )
    assert all(task.is_current for task in tasks)
    assert len({(task.title, task.day, task.number) for task in tasks}) == len(tasks)
    other_task = session.execute(
        select(DailyTaskOrm).where(DailyTaskOrm.user_id == other)
    ).scalar_one()
    assert other_task.is_current is False


@pytest.mark.asyncio
async def test_psychologist_pagination_counts_same_role_and_tags(memory_db):
    db, session = memory_db
    tags = [InquiryOrm(text="tag1"), InquiryOrm(text="tag2")]
    session.add_all(tags)
    session.flush()
    for index in range(5):
        session.add(
            UsersOrm(
                id=uuid4(),
                username=f"psych{index}",
                email=f"p{index}@example.com",
                gender="male",
                role_id=2,
                inquiries=tags if index < 3 else [tags[0]],
            )
        )
    session.add(
        UsersOrm(
            id=uuid4(),
            username="HR",
            email="hr@example.com",
            gender="male",
            role_id=3,
            inquiries=tags,
        )
    )
    session.commit()
    service = PsychologistService(db)
    unfiltered = await service.get_all_psychologists(page=2, per_page=2)
    filtered = await service.get_all_psychologists(
        page=2, per_page=2, inquiry_ids=[tag.id for tag in tags]
    )
    unpaginated = await service.get_all_psychologists(
        inquiry_ids=[tag.id for tag in tags]
    )
    empty = await service.get_all_psychologists(per_page=2, inquiry_ids=[9999])
    assert (unfiltered["total"], unfiltered["pages"], len(unfiltered["items"])) == (
        5,
        3,
        2,
    )
    assert (filtered["total"], filtered["pages"], len(filtered["items"])) == (3, 2, 1)
    assert (unpaginated["total"], len(unpaginated["items"])) == (3, 3)
    assert (empty["total"], empty["pages"], empty["items"]) == (0, 0, [])


@pytest.mark.asyncio
async def test_statistics_count_all_exercise_completions_for_current_user(memory_db):
    db, session = memory_db
    owner, other = uuid4(), uuid4()
    exercises = []
    for index in range(2):
        exercise = ExerciseStructureOrm(
            id=uuid4(),
            title=f"exercise{index}",
            description="description",
            picture_link="/image.png",
            time_to_read=1,
            questions_count=0,
            sort_order=index,
            group=0,
        )
        exercises.append(exercise)
        session.add(exercise)
    session.flush()
    for user_id, exercise in [
        (owner, exercises[0]),
        (owner, exercises[0]),
        (owner, exercises[1]),
        (other, exercises[0]),
    ]:
        session.add(
            CompletedExerciseOrm(
                id=uuid4(),
                user_id=user_id,
                exercise_structure_id=exercise.id,
                date=datetime.now(),
            )
        )
    session.commit()
    for repository in ("test_result", "mood_tracker", "education_progress"):
        setattr(
            db, repository, SimpleNamespace(get_filtered=AsyncMock(return_value=[]))
        )
    stats = await StatisticsService(db).get_user_activity_statistics(owner)
    assert stats["exercises"] == {
        "total_exercises": 3,
        "by_exercise": {"exercise0": 2, "exercise1": 1},
    }
    assert stats["total_activities"] == 3
    assert (await StatisticsService(db)._get_exercise_statistics(uuid4()))[
        "total_exercises"
    ] == 0


@pytest.mark.asyncio
async def test_statistics_does_not_hide_database_failure_as_zero():
    db = SimpleNamespace(
        exercise=SimpleNamespace(
            get_completion_counts=AsyncMock(
                side_effect=RuntimeError("database unavailable")
            )
        )
    )
    with pytest.raises(MyAppException):
        await StatisticsService(db)._get_exercise_statistics(uuid4())
