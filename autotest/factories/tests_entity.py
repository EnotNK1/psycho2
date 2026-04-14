import datetime
import uuid
from types import SimpleNamespace


TEST_ID = uuid.UUID("10101010-1010-1010-1010-101010101010")
SECOND_TEST_ID = uuid.UUID("20202020-2020-2020-2020-202020202020")
QUESTION_ID = uuid.UUID("30303030-3030-3030-3030-303030303030")
SECOND_QUESTION_ID = uuid.UUID("40404040-4040-4040-4040-404040404040")
ANSWER_ID = uuid.UUID("50505050-5050-5050-5050-505050505050")
SECOND_ANSWER_ID = uuid.UUID("60606060-6060-6060-6060-606060606060")
SCALE_ID = uuid.UUID("70707070-7070-7070-7070-707070707070")
SECOND_SCALE_ID = uuid.UUID("80808080-8080-8080-8080-808080808080")
BORDER_ID = uuid.UUID("90909090-9090-9090-9090-909090909090")
SECOND_BORDER_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")
RESULT_ID = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
SECOND_RESULT_ID = uuid.UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff")
USER_ID = uuid.UUID("99999999-9999-9999-9999-999999999999")
SECOND_USER_ID = uuid.UUID("12121212-1212-1212-1212-121212121212")


def make_test(
    *,
    test_id=TEST_ID,
    title="Burnout Test",
    description="Long description",
    short_desc="Short description",
    link="/images/test.png",
):
    return SimpleNamespace(
        id=test_id,
        title=title,
        description=description,
        short_desc=short_desc,
        link=link,
    )


def make_question(
    *,
    question_id=QUESTION_ID,
    test_id=TEST_ID,
    text="Question text",
    opposite_text="Opposite text",
    number=1,
    answer_choice=None,
):
    return SimpleNamespace(
        id=question_id,
        text=text,
        opposite_text=opposite_text,
        number=number,
        test_id=test_id,
        answer_choice=answer_choice or [ANSWER_ID, SECOND_ANSWER_ID],
    )


def make_answer(*, answer_id=ANSWER_ID, text="Never", score=0):
    return SimpleNamespace(
        id=answer_id,
        text=text,
        score=score,
    )


def make_scale(*, scale_id=SCALE_ID, test_id=TEST_ID, title="Scale A", min_score=0, max_score=30):
    return SimpleNamespace(
        id=scale_id,
        test_id=test_id,
        title=title,
        min=min_score,
        max=max_score,
    )


def make_border(
    *,
    border_id=BORDER_ID,
    scale_id=SCALE_ID,
    left_border=0,
    right_border=10,
    color="#00AA00",
    title="Norm",
    user_recommendation="Take care",
):
    return SimpleNamespace(
        id=border_id,
        scale_id=scale_id,
        left_border=left_border,
        right_border=right_border,
        color=color,
        title=title,
        user_recommendation=user_recommendation,
    )


def make_test_result_row(
    *,
    result_id=RESULT_ID,
    test_id=TEST_ID,
    user_id=USER_ID,
    date=datetime.datetime(2026, 4, 15, 10, 0, 0),
):
    return SimpleNamespace(
        id=result_id,
        test_id=test_id,
        user_id=user_id,
        date=date,
    )


def make_scale_result_row(*, result_id=RESULT_ID, scale_id=SCALE_ID, score=7):
    return SimpleNamespace(
        id=uuid.uuid4(),
        test_result_id=result_id,
        scale_id=scale_id,
        score=score,
    )


def build_test_result_request(
    *,
    test_id=TEST_ID,
    date="2026-04-15T10:00:00",
    results=None,
):
    return {
        "test_id": str(test_id),
        "date": date,
        "results": results or [0, 1],
    }

