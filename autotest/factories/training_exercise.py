import uuid
from types import SimpleNamespace


EXERCISE_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
SECOND_EXERCISE_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def make_exercise(exercise_id=EXERCISE_ID, title="Detector"):
    return SimpleNamespace(
        id=exercise_id,
        title=title,
        picture_link="/image.png",
        description="Description",
        time_to_read=7,
    )


def sample_seed_fixture():
    return [
        {
            "id": str(EXERCISE_ID),
            "title": "Detector",
            "description": "Description",
            "picture_link": "/image.png",
            "time_to_read": 5,
            "questions": [
                {
                    "text": "Question 1",
                    "variants": [
                        {"title": "A", "correct": True, "explanation": "ok"},
                        {"title": "B", "correct": False, "explanation": "no"},
                    ],
                }
            ],
        }
    ]
