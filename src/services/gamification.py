import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional
import logging

from src.services.base import BaseService

logger = logging.getLogger(__name__)


class GamificationService(BaseService):

    async def get_current_score(self, user_id: uuid.UUID) -> int:
        """Получить текущий score пользователя"""
        try:
            return await self.db.user_score.get_current_score(user_id)
        except Exception as e:
            logger.error(
                f"Error getting current score for user {user_id}: {e}")
            return 0

    async def get_weekly_scores(self, user_id: uuid.UUID) -> List[dict]:
        """Получить scores за последнюю неделю"""
        try:
            return await self.db.user_score.get_weekly_scores(user_id)
        except Exception as e:
            logger.error(
                f"Error getting weekly scores for user {user_id}: {e}")
            return []

    async def get_scores_by_period(self, user_id: uuid.UUID, start_date: date, end_date: date) -> List[dict]:
        """Получить scores за указанный период"""
        try:
            # Валидация дат
            if start_date > end_date:
                raise ValueError("Start date cannot be after end date")

            if start_date > date.today():
                raise ValueError("Start date cannot be in the future")

            return await self.db.user_score.get_scores_by_period(user_id, start_date, end_date)
        except Exception as e:
            logger.error(
                f"Error getting scores for period for user {user_id}: {e}")
            raise

    async def add_points_for_activity(self, user_id: uuid.UUID, activity_type: str) -> int:
        """Добавить 10 баллов за активность пользователя"""
        try:
            POINTS_PER_ACTIVITY = 10
            new_score = await self.db.user_score.update_current_score(user_id, POINTS_PER_ACTIVITY)

            logger.info(
                f"Added {POINTS_PER_ACTIVITY} points for {activity_type} to user {user_id}. New score: {new_score}")
            return new_score

        except Exception as e:
            logger.error(
                f"Error adding points for activity to user {user_id}: {e}")
            return await self.db.user_score.get_current_score(user_id)

    async def archive_daily_scores(self):
        """Архивировать scores за прошедший день (вызывается в 00:00)"""
        try:
            await self.db.user_score.archive_yesterday_scores()
            logger.info("Daily scores archived successfully")
        except Exception as e:
            logger.error(f"Error archiving daily scores: {e}")
            raise
