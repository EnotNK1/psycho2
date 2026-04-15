import datetime
import uuid
from types import SimpleNamespace


USER_ID = uuid.UUID("13131313-1313-1313-1313-131313131313")
SECOND_USER_ID = uuid.UUID("14141414-1414-1414-1414-141414141414")
MOOD_TRACKER_ID = uuid.UUID("15151515-1515-1515-1515-151515151515")
SECOND_MOOD_TRACKER_ID = uuid.UUID("16161616-1616-1616-1616-161616161616")


def build_add_mood_payload(*, score=55, day="2026-04-15", emoji_ids=None):
    return {
        "score": score,
        "day": day,
        "emoji_ids": emoji_ids or [1, 2],
    }


def make_mood_tracker(
    *,
    mood_tracker_id=MOOD_TRACKER_ID,
    score=55,
    created_at=datetime.datetime(2026, 4, 15, 10, 0, 0),
    user_id=USER_ID,
    emoji_ids=None,
):
    return SimpleNamespace(
        id=mood_tracker_id,
        score=score,
        created_at=created_at,
        user_id=user_id,
        emoji_ids=emoji_ids or [1, 2],
    )


def build_mood_tracker_response(
    *,
    mood_tracker_id=MOOD_TRACKER_ID,
    score=55,
    created_at="2026-04-15T10:00:00",
    user_id=USER_ID,
    emoji_ids=None,
    emoji_texts=None,
):
    return {
        "id": str(mood_tracker_id),
        "score": score,
        "created_at": created_at,
        "user_id": str(user_id),
        "emoji_ids": emoji_ids or [1, 2],
        "emoji_texts": emoji_texts or ["happy", "calm"],
    }


def make_emoji(*, emoji_id=1, text="happy"):
    return SimpleNamespace(id=emoji_id, text=text)

