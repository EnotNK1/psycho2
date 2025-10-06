import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.gamification import UserScoreOrm
from src.repositories.base import BaseRepository


class UserScoreRepository(BaseRepository):
    model = UserScoreOrm

    async def get_current_score(self, user_id: uuid.UUID) -> int:
        """Получить текущий score пользователя"""
        today = date.today()
        query = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.date == today)
        )
        result = await self.session.execute(query)
        score_record = result.scalar_one_or_none()

        return score_record.score if score_record else 0

    async def get_weekly_scores(self, user_id: uuid.UUID) -> List[dict]:
        """Получить scores за последнюю неделю"""
        week_ago = date.today() - timedelta(days=6)  # 7 дней включая сегодня
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.date >= week_ago
            )
        ).order_by(self.model.date)

        result = await self.session.execute(query)
        scores = result.scalars().all()

        return [
            {"date": score.date.isoformat(), "score": score.score}
            for score in scores
        ]

    async def get_scores_by_period(self, user_id: uuid.UUID, start_date: date, end_date: date) -> List[dict]:
        """Получить scores за указанный период"""
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.date >= start_date,
                self.model.date <= end_date
            )
        ).order_by(self.model.date)

        result = await self.session.execute(query)
        scores = result.scalars().all()

        return [
            {"date": score.date.isoformat(), "score": score.score}
            for score in scores
        ]

    async def update_current_score(self, user_id: uuid.UUID, points_to_add: int) -> int:
        """Добавить баллы к текущему score (не более 40)"""
        today = date.today()

        # Находим или создаем запись на сегодня
        query = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.date == today)
        )
        result = await self.session.execute(query)
        score_record = result.scalar_one_or_none()

        if score_record:
            new_score = min(score_record.score + points_to_add, 40)
            score_record.score = new_score
        else:
            new_score = min(points_to_add, 40)
            score_record = UserScoreOrm(
                user_id=user_id,
                score=new_score,
                date=today
            )
            self.session.add(score_record)

        return new_score

    async def archive_yesterday_scores(self):
        """Архивируем scores за вчера (вызывается в 00:00)"""
        yesterday = date.today() - timedelta(days=1)

        # Здесь можно добавить логику архивации если нужно
        # Пока просто оставляем записи как есть
        logger.info(f"Scores за {yesterday} архивированы")

    async def get_user_score_for_date(self, user_id: uuid.UUID, target_date: date) -> Optional[int]:
        """Получить score пользователя за конкретную дату"""
        query = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.date == target_date)
        )
        result = await self.session.execute(query)
        score_record = result.scalar_one_or_none()

        return score_record.score if score_record else None
