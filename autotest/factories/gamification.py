import uuid
from datetime import date, timedelta


USER_ID = uuid.UUID("51515151-5151-5151-5151-515151515151")
SECOND_USER_ID = uuid.UUID("52525252-5252-5252-5252-525252525252")
SCORE_ID = uuid.UUID("53535353-5353-5353-5353-535353535353")
SECOND_SCORE_ID = uuid.UUID("54545454-5454-5454-5454-545454545454")


def build_score_entry(score_date=None, score=10):
    return {
        "date": (score_date or date.today()).isoformat(),
        "score": score,
    }


def build_current_score_response(score=10):
    return {"score": score}


def build_scores_response(entries=None):
    return {"scores": entries if entries is not None else [build_score_entry()]}


def build_praise_response(consecutive_days=0, title="", subtitle=""):
    return {
        "consecutive_days": consecutive_days,
        "title": title,
        "subtitle": subtitle,
    }


def build_score_rows(days, *, start_date=None, score=30):
    start = start_date or date.today()
    return [
        {"date": (start - timedelta(days=offset)).isoformat(), "score": score}
        for offset in range(days)
    ]
