import uuid
from datetime import date
from typing import Optional

from sqlalchemy import and_, select

from src.models.gamification import UserScoreOrm
from src.repositories.base import BaseRepository


class UserScoreRepository(BaseRepository):
    model = UserScoreOrm

    async def get_by_user_and_date(
        self, user_id: uuid.UUID, target_date: date
    ) -> Optional[UserScoreOrm]:
        """Get a user's score record for a specific date."""
        query = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.date == target_date)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_scores_by_period(
        self, user_id: uuid.UUID, start_date: date, end_date: date
    ) -> list[UserScoreOrm]:
        """Get score records for a user within a date range."""
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.date >= start_date,
                self.model.date <= end_date,
            )
        ).order_by(self.model.date)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(
        self, user_id: uuid.UUID, score: int, target_date: date
    ) -> UserScoreOrm:
        """Create a score record for a specific date."""
        score_record = UserScoreOrm(user_id=user_id, score=score, date=target_date)
        self.session.add(score_record)
        await self.session.flush()
        return score_record

    async def update_score(
        self, score_record: UserScoreOrm, new_score: int
    ) -> UserScoreOrm:
        """Update an existing score record."""
        score_record.score = new_score
        await self.session.flush()
        return score_record

    async def archive_yesterday_scores(self):
        """Placeholder for future daily archive logic."""
        return None

    async def get_user_score_for_date(
        self, user_id: uuid.UUID, target_date: date
    ) -> Optional[int]:
        """Return the score value for a specific date."""
        score_record = await self.get_by_user_and_date(user_id, target_date)
        return score_record.score if score_record else None
