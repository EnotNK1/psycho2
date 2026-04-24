import datetime
import uuid
from types import SimpleNamespace

from src.enums import FieldType, ViewType


EXERCISE_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
SECOND_EXERCISE_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
FIELD_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
SECOND_FIELD_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
VARIANT_ID = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
VIEW_ID = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
RESULT_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")
USER_ID = uuid.UUID("99999999-9999-9999-9999-999999999999")


def build_exercise_payload(**overrides):
    payload = {
        "title": "Free writing",
        "description": "Describe your day",
        "picture_link": "/images/exercise.png",
        "time_to_read": 5,
        "questions_count": 2,
        "linked_exercise_id": None,
    }
    payload.update(overrides)
    return payload


def build_field_payload(**overrides):
    payload = {
        "title": "Mood reason",
        "major": True,
        "view": ViewType.DEFAULT.value,
        "type": FieldType.INPUT.value,
        "placeholder": "Write here",
        "prompt": "What happened?",
        "description": "Main input",
        "order": 1,
        "exercises": [str(SECOND_EXERCISE_ID)],
    }
    payload.update(overrides)
    return payload


def build_variant_payload(**overrides):
    payload = {"title": "Variant A"}
    payload.update(overrides)
    return payload


def build_view_payload(**overrides):
    payload = {
        "view": "success",
        "score": 10,
        "picture_link": "/images/success.png",
        "message": "Exercise completed",
    }
    payload.update(overrides)
    return payload


def build_complete_payload(**overrides):
    payload = {
        "exercise_structure_id": str(EXERCISE_ID),
        "filled_fields": [
            {
                "field_id": str(FIELD_ID),
                "text": "My answer",
            }
        ],
    }
    payload.update(overrides)
    return payload


def build_exercise_response(**overrides):
    response = {
        "id": str(EXERCISE_ID),
        "title": "Free writing",
        "picture_link": "/images/exercise.png",
        "open": True,
    }
    response.update(overrides)
    return response


def build_exercise_detail_response(**overrides):
    response = {
        "id": str(EXERCISE_ID),
        "title": "Free writing",
        "picture_link": "/images/exercise.png",
        "description": "Describe your day",
        "time_to_read": 5,
        "questions_count": 2,
        "open": True,
    }
    response.update(overrides)
    return response


def build_field_response(**overrides):
    response = {
        "id": str(FIELD_ID),
        "title": "Mood reason",
        "major": True,
        "view": ViewType.DEFAULT.value,
        "type": FieldType.INPUT.value,
        "placeholder": "Write here",
        "prompt": "What happened?",
        "description": "Main input",
        "order": 1,
        "exercises": [str(SECOND_EXERCISE_ID)],
        "exercise_structure_id": str(EXERCISE_ID),
        "variants": [],
    }
    response.update(overrides)
    return response


def build_variant_response(**overrides):
    response = {
        "id": str(VARIANT_ID),
        "title": "Variant A",
        "field_id": str(FIELD_ID),
    }
    response.update(overrides)
    return response


def build_view_response(**overrides):
    response = {
        "view": "success",
        "score": 10,
        "picture_link": "/images/success.png",
        "message": "Exercise completed",
        "open": False,
    }
    response.update(overrides)
    return response


def build_structure_response(**overrides):
    response = {
        **build_exercise_detail_response(),
        "pulled_fields": [],
        "pages": [
            {
                "page_number": 1,
                "sections": [
                    {
                        "id": str(FIELD_ID),
                        "title": "Mood reason",
                        "view": ViewType.DEFAULT.value,
                        "type": FieldType.INPUT.value,
                        "placeholder": "Write here",
                        "prompt": "What happened?",
                        "variants": [build_variant_response()],
                    }
                ],
            }
        ],
    }
    response.update(overrides)
    return response


def build_results_response(**overrides):
    response = {
        "results": [
            {
                "id": str(RESULT_ID),
                "exercise_id": str(EXERCISE_ID),
                "date": "2026-04-01",
                "preview": "My answer",
            }
        ]
    }
    response.update(overrides)
    return response


def build_result_detail_response(**overrides):
    response = {
        "id": str(RESULT_ID),
        "title": "Free writing",
        "picture_link": "/images/exercise.png",
        "description": "Describe your day",
        "exercise_id": str(EXERCISE_ID),
        "date": "2026-04-01",
        "sections": [
            {
                "title": "Mood reason",
                "view": ViewType.DEFAULT.value,
                "type": FieldType.INPUT.value,
                "value": "My answer",
            }
        ],
    }
    response.update(overrides)
    return response


def build_completed_response(**overrides):
    response = {
        "id": str(RESULT_ID),
        "score": 10,
        "picture_link": "/images/success.png",
        "view": "success",
        "success_message": "Exercise completed",
    }
    response.update(overrides)
    return response


def make_exercise_orm_like(
    exercise_id=EXERCISE_ID,
    *,
    linked_exercise_id=None,
    fields=None,
):
    return SimpleNamespace(
        id=exercise_id,
        title="Free writing",
        description="Describe your day",
        picture_link="/images/exercise.png",
        time_to_read=5,
        questions_count=2,
        linked_exercise_id=linked_exercise_id,
        field=fields or [],
    )


def make_field_orm_like(field_id=FIELD_ID, *, variants=None, exercises=None, major=True):
    return SimpleNamespace(
        id=field_id,
        title="Mood reason",
        major=major,
        view=ViewType.DEFAULT.value,
        type=FieldType.INPUT.value,
        placeholder="Write here",
        prompt="What happened?",
        description="Main input",
        order=1,
        exercise_structure_id=EXERCISE_ID,
        variants=variants or [],
        exercises=exercises,
    )


def make_variant_orm_like(variant_id=VARIANT_ID):
    return SimpleNamespace(id=variant_id, title="Variant A", field_id=FIELD_ID)


def make_completed_orm_like(result_id=RESULT_ID, *, filled_fields=None):
    return SimpleNamespace(
        id=result_id,
        exercise_structure_id=EXERCISE_ID,
        user_id=USER_ID,
        date=datetime.datetime(2026, 4, 1, 12, 0),
        filled_field=filled_fields or [],
    )


def make_filled_field_orm_like(field_id=FIELD_ID, *, text="My answer", major=True):
    return SimpleNamespace(
        id=uuid.uuid4(),
        title="Mood reason",
        view=ViewType.DEFAULT.value,
        type=FieldType.INPUT.value,
        text=text,
        field_id=field_id,
        major=major,
        exercises=None,
    )
