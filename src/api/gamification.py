import uuid
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.api.dependencies.db import DBDep
from src.api.dependencies.user_id import UserIdDep
from src.schemas.gamification import (
    CurrentScoreResponse,
    PeriodScoresResponse,
    PraiseResponse,
    WeeklyScoresResponse,
)
from src.services.gamification import GamificationService

router = APIRouter(prefix="/gamification", tags=["Геймификация"])
PRAISE_SCORE_THRESHOLD = 20
PRAISE_LOOKBACK_DAYS = 30


def _normalize_user_id(user_id: uuid.UUID | str) -> uuid.UUID:
    if isinstance(user_id, uuid.UUID):
        return user_id
    return uuid.UUID(str(user_id))


def _score_item_date(item: Any) -> date | None:
    raw_date = item.get("date") if isinstance(item, dict) else getattr(item, "date", None)
    if isinstance(raw_date, date):
        return raw_date
    if isinstance(raw_date, str):
        try:
            return date.fromisoformat(raw_date)
        except ValueError:
            return None
    return None


def _score_item_value(item: Any) -> int:
    return item.get("score", 0) if isinstance(item, dict) else getattr(item, "score", 0)


def _build_praise(consecutive_days: int) -> PraiseResponse:
    if consecutive_days >= 30:
        return PraiseResponse(
            consecutive_days=30,
            title="Осознанный месяц",
            subtitle="Это месяц, выбранный для себя. Спасибо, что ты с нами!",
        )
    if consecutive_days >= 14:
        return PraiseResponse(
            consecutive_days=14,
            title="Две недели заботы",
            subtitle="Ты мягко возвращаешься к себе снова и снова",
        )
    if consecutive_days >= 7:
        return PraiseResponse(
            consecutive_days=7,
            title="Неделя рядом с собой",
            subtitle="Ритм пойман, он тебя поддерживает",
        )
    if consecutive_days >= 3:
        return PraiseResponse(
            consecutive_days=3,
            title="Ты на верном пути",
            subtitle="Мы рады тебе! Продолжай в своем темпе",
        )
    return PraiseResponse(consecutive_days=consecutive_days, title="", subtitle="")


def _build_praise_from_scores(scores: list[Any], end_date: date) -> PraiseResponse:
    praise_score_threshold = getattr(
        GamificationService,
        "PRAISE_SCORE_THRESHOLD",
        PRAISE_SCORE_THRESHOLD,
    )
    score_by_date = {
        item_date: _score_item_value(item)
        for item in scores
        if (item_date := _score_item_date(item)) is not None
    }

    consecutive_days = 0
    current_date = end_date
    while score_by_date.get(current_date, 0) > praise_score_threshold:
        consecutive_days += 1
        current_date -= timedelta(days=1)

    return _build_praise(consecutive_days)


@router.get("/current-score", response_model=CurrentScoreResponse)
async def get_current_score(
    db: DBDep,
    user_id: UserIdDep,
):
    """Получить текущий score пользователя."""
    try:
        normalized_user_id = _normalize_user_id(user_id)
        score = await GamificationService(db).get_current_score(normalized_user_id)
        return CurrentScoreResponse(score=score)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekly-scores", response_model=WeeklyScoresResponse)
async def get_weekly_scores(
    db: DBDep,
    user_id: UserIdDep,
):
    """Получить scores за последнюю неделю."""
    try:
        normalized_user_id = _normalize_user_id(user_id)
        scores = await GamificationService(db).get_weekly_scores(normalized_user_id)
        return WeeklyScoresResponse(scores=scores)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/period-scores", response_model=PeriodScoresResponse)
async def get_period_scores(
    start_date: date = Query(..., description="Начальная дата (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Конечная дата (YYYY-MM-DD)"),
    *,
    db: DBDep,
    user_id: UserIdDep,
):
    """Получить scores за указанный период."""
    try:
        normalized_user_id = _normalize_user_id(user_id)
        scores = await GamificationService(db).get_scores_by_period(
            normalized_user_id, start_date, end_date
        )
        return PeriodScoresResponse(scores=scores)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/praise", response_model=PraiseResponse)
async def get_praise(
    db: DBDep,
    user_id: UserIdDep,
):
    try:
        normalized_user_id = _normalize_user_id(user_id)
        end_date = date.today()
        lookback_days = getattr(
            GamificationService,
            "PRAISE_LOOKBACK_DAYS",
            PRAISE_LOOKBACK_DAYS,
        )
        start_date = end_date - timedelta(days=lookback_days)
        scores = await GamificationService(db).get_scores_by_period(
            normalized_user_id, start_date, end_date
        )
        return _build_praise_from_scores(scores, end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
