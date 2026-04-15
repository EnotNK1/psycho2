from datetime import datetime
from uuid import UUID


USER_ID = UUID("18181818-1818-1818-1818-181818181818")
DIARY_ID = UUID("19191919-1919-1919-1919-191919191919")
SECOND_DIARY_ID = UUID("20202020-2020-2020-2020-202020202020")


def build_add_diary_payload(text="Diary note", day="2026-04-15"):
    return {
        "text": text,
        "day": day,
    }


def build_diary_response(
    diary_id=DIARY_ID,
    text="Diary note",
    created_at="2026-04-15T10:30:00",
    user_id=USER_ID,
):
    return {
        "id": str(diary_id),
        "text": text,
        "created_at": created_at,
        "user_id": str(user_id),
    }


def make_diary(
    diary_id=DIARY_ID,
    text="Diary note",
    created_at=None,
    user_id=USER_ID,
):
    return type(
        "DiaryObj",
        (),
        {
            "id": diary_id,
            "text": text,
            "created_at": created_at or datetime(2026, 4, 15, 10, 30, 0),
            "user_id": user_id,
        },
    )()

