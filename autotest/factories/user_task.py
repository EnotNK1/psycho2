import uuid
from datetime import datetime
from types import SimpleNamespace


USER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TASK_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
OTHER_TASK_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


def make_task(
    task_id=TASK_ID,
    text="Task",
    created_at=datetime(2026, 4, 10, 12, 0, 0),
    completed_at=None,
    is_complete=False,
    user_id=USER_ID,
):
    return SimpleNamespace(
        id=task_id,
        text=text,
        created_at=created_at,
        completed_at=completed_at,
        is_complete=is_complete,
        user_id=user_id,
    )


def build_actual_task_payload(task_id=TASK_ID, user_id=USER_ID, text="Task", created_at=None):
    timestamp = created_at or datetime(2026, 4, 10, 12, 0, 0)
    return {
        "id": str(task_id),
        "text": text,
        "created_at": timestamp.isoformat(),
        "is_complete": False,
        "user_id": str(user_id),
    }


def build_completed_task_payload(task_id=TASK_ID, user_id=USER_ID, text="Done", completed_at=None):
    timestamp = completed_at or datetime(2026, 4, 10, 12, 0, 0)
    return {
        "id": str(task_id),
        "text": text,
        "created_at": timestamp.isoformat(),
        "completed_at": timestamp.isoformat(),
        "is_complete": True,
        "user_id": str(user_id),
    }
