from datetime import date, datetime, timedelta
from typing import List
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException

from src.api.dependencies.db import get_db, DBDep
from src.api.dependencies.user_id import get_current_user_id, UserIdDep
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

@router.get("/praise")
async def get_praise(
        db: DBDep,
        user_id: UserIdDep
):
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        scores = await GamificationService(db).get_scores_by_period(user_id, start_date, end_date)

        processed = []
        for item in scores:
            raw_date = item['date']
            if isinstance(raw_date, datetime):
                dt_date = raw_date.date()
            elif isinstance(raw_date, date):
                dt_date = raw_date
            elif isinstance(raw_date, str):
                dt_date = datetime.fromisoformat(raw_date).date()
            else:
                continue
            processed.append((dt_date, item['score']))

        processed.sort(key=lambda x: x[0])

        consecutive_days = 0
        if processed:
            expected_date = processed[-1][0]
            for current_date, current_score in reversed(processed):
                if current_score > 20:
                    if consecutive_days == 0 or current_date == expected_date:
                        consecutive_days += 1
                        expected_date = current_date - timedelta(days=1)
                    else:
                        break
                else:
                    break

        K = consecutive_days

        if K == 30:
            title = "Осознанный месяц"
            subtitle = "Это месяц, выбранный для себя. Спасибо, что ты с нами!"
        elif K == 14:
            title = "Две недели заботы"
            subtitle = "Ты мягко возвращаешься к себе снова и снова"
        elif K == 7:
            title = "Неделя рядом с собой"
            subtitle = "Ритм пойман, он тебя поддерживает"
        elif K == 3:
            title = "Ты на верном пути"
            subtitle = "Мы рады тебе! Продолжай в своем темпе"
        else:
            title = ""
            subtitle = ""

        return {
            "consecutive_days": K,
            "title": title,
            "subtitle": subtitle
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))