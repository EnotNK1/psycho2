from datetime import date

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


@router.get("/current-score", response_model=CurrentScoreResponse)
async def get_current_score(
    db: DBDep,
    user_id: UserIdDep,
):
    """Получить текущий score пользователя."""
    try:
        score = await GamificationService(db).get_current_score(user_id)
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
        scores = await GamificationService(db).get_weekly_scores(user_id)
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
        scores = await GamificationService(db).get_scores_by_period(
            user_id, start_date, end_date
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
        return await GamificationService(db).get_praise(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
