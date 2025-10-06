from datetime import date
from typing import List
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException

from src.api.dependencies.db import get_db
from src.api.dependencies.user_id import get_current_user_id
from src.services.gamification import GamificationService
from src.schemas.gamification import (
    CurrentScoreResponse,
    WeeklyScoresResponse,
    PeriodScoresResponse,
    AddPointsRequest
)

router = APIRouter(prefix="/gamification", tags=["Геймификация"])


@router.get("/current-score", response_model=CurrentScoreResponse)
async def get_current_score(
    db=Depends(get_db),
    # Переименуем, так как это ID
    current_user_id: str = Depends(get_current_user_id)
):
    """Получить текущий score пользователя"""
    try:
        user_id = uuid.UUID(current_user_id)  # Конвертируем строку в UUID
        score = await GamificationService(db).get_current_score(user_id)
        return CurrentScoreResponse(score=score)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekly-scores", response_model=WeeklyScoresResponse)
async def get_weekly_scores(
    db=Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)  # Переименуем
):
    """Получить scores за последнюю неделю"""
    try:
        user_id = uuid.UUID(current_user_id)
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
    db=Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)  # Переименуем
):
    """Получить scores за указанный период"""
    try:
        user_id = uuid.UUID(current_user_id)
        scores = await GamificationService(db).get_scores_by_period(
            user_id, start_date, end_date
        )
        return PeriodScoresResponse(scores=scores)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
