import logging
import uuid
from datetime import date, timedelta
from typing import Iterable

from src.models.gamification import UserScoreOrm
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class GamificationService(BaseService):
    POINTS_PER_ACTIVITY = 10
    MAX_DAILY_SCORE = 40
    PRAISE_SCORE_THRESHOLD = 20
    PRAISE_LOOKBACK_DAYS = 30

    @staticmethod
    def _normalize_user_id(user_id: uuid.UUID | str) -> uuid.UUID:
        if isinstance(user_id, uuid.UUID):
            return user_id
        return uuid.UUID(str(user_id))

    @staticmethod
    def _serialize_scores(scores: Iterable[UserScoreOrm]) -> list[dict]:
        return [
            {"date": score.date.isoformat(), "score": score.score}
            for score in scores
        ]

    @staticmethod
    def _build_dense_scores(
        start_date: date, end_date: date, scores: Iterable[UserScoreOrm]
    ) -> list[dict]:
        score_by_date = {score.date: score.score for score in scores}
        total_days = (end_date - start_date).days + 1
        return [
            {
                "date": (start_date + timedelta(days=offset)).isoformat(),
                "score": score_by_date.get(start_date + timedelta(days=offset), 0),
            }
            for offset in range(total_days)
        ]

    @staticmethod
    def _build_praise(consecutive_days: int) -> dict:
        if consecutive_days == 30:
            return {
                "consecutive_days": consecutive_days,
                "title": "Осознанный месяц",
                "subtitle": "Это месяц, выбранный для себя. Спасибо, что ты с нами!",
            }
        if consecutive_days == 14:
            return {
                "consecutive_days": consecutive_days,
                "title": "Две недели заботы",
                "subtitle": "Ты мягко возвращаешься к себе снова и снова",
            }
        if consecutive_days == 7:
            return {
                "consecutive_days": consecutive_days,
                "title": "Неделя рядом с собой",
                "subtitle": "Ритм пойман, он тебя поддерживает",
            }
        if consecutive_days == 3:
            return {
                "consecutive_days": consecutive_days,
                "title": "Ты на верном пути",
                "subtitle": "Мы рады тебе! Продолжай в своем темпе",
            }
        return {"consecutive_days": consecutive_days, "title": "", "subtitle": ""}

    async def get_current_score(self, user_id: uuid.UUID | str) -> int:
        """Get the user's score for today."""
        try:
            normalized_user_id = self._normalize_user_id(user_id)
            today_score = await self.db.user_score.get_by_user_and_date(
                normalized_user_id, date.today()
            )
            return today_score.score if today_score else 0
        except Exception as e:
            logger.error(
                f"Error getting current score for user {user_id}: {e}")
            return 0

    async def get_weekly_scores(self, user_id: uuid.UUID | str) -> list[dict]:
        """Get scores for the last 7 days including today."""
        try:
            normalized_user_id = self._normalize_user_id(user_id)
            end_date = date.today()
            start_date = end_date - timedelta(days=6)
            scores = await self.db.user_score.get_scores_by_period(
                normalized_user_id, start_date, end_date
            )
            return self._build_dense_scores(start_date, end_date, scores)
        except Exception as e:
            logger.error(
                f"Error getting weekly scores for user {user_id}: {e}")
            return []

    async def get_scores_by_period(
        self, user_id: uuid.UUID | str, start_date: date, end_date: date
    ) -> list[dict]:
        """Get scores for the requested period."""
        try:
            if start_date > end_date:
                raise ValueError("Start date cannot be after end date")
            if start_date > date.today():
                raise ValueError("Start date cannot be in the future")

            normalized_user_id = self._normalize_user_id(user_id)
            scores = await self.db.user_score.get_scores_by_period(
                normalized_user_id, start_date, end_date
            )
            return self._build_dense_scores(start_date, end_date, scores)
        except Exception as e:
            logger.error(
                f"Error getting scores for period for user {user_id}: {e}")
            raise

    async def add_points_for_activity(
        self, user_id: uuid.UUID | str, activity_type: str
    ) -> int:
        """Add fixed points for an activity while respecting the daily cap."""
        try:
            normalized_user_id = self._normalize_user_id(user_id)
            today = date.today()
            today_score = await self.db.user_score.get_by_user_and_date(
                normalized_user_id, today
            )

            current_score = today_score.score if today_score else 0
            new_score = min(
                current_score + self.POINTS_PER_ACTIVITY, self.MAX_DAILY_SCORE
            )

            if today_score:
                await self.db.user_score.update_score(today_score, new_score)
            else:
                await self.db.user_score.create(normalized_user_id, new_score, today)

            logger.info(
                "Added %s points for %s to user %s. New score: %s",
                self.POINTS_PER_ACTIVITY,
                activity_type,
                user_id,
                new_score,
            )
            return new_score
        except Exception as e:
            logger.error(
                f"Error adding points for activity to user {user_id}: {e}"
            )
            return await self.get_current_score(user_id)

    async def get_praise(self, user_id: uuid.UUID | str) -> dict:
        """Build praise information based on the current streak."""
        normalized_user_id = self._normalize_user_id(user_id)
        end_date = date.today()
        start_date = end_date - timedelta(days=self.PRAISE_LOOKBACK_DAYS)

        scores = await self.db.user_score.get_scores_by_period(
            normalized_user_id, start_date, end_date
        )
        if not scores:
            return self._build_praise(0)

        processed = sorted(
            ((score.date, score.score) for score in scores),
            key=lambda item: item[0],
        )

        consecutive_days = 0
        expected_date = processed[-1][0]
        for current_date, current_score in reversed(processed):
            if current_score <= self.PRAISE_SCORE_THRESHOLD:
                break
            if consecutive_days != 0 and current_date != expected_date:
                break
            consecutive_days += 1
            expected_date = current_date - timedelta(days=1)

        return self._build_praise(consecutive_days)

    async def archive_daily_scores(self):
        """Archive daily scores if archive logic is added later."""
        try:
            await self.db.user_score.archive_yesterday_scores()
            logger.info("Daily scores archived successfully")
        except Exception as e:
            logger.error(f"Error archiving daily scores: {e}")
            raise
