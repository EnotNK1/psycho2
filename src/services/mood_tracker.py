import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import func

from src.exceptions import (
    ScoreOutOfRangeError,
    ObjectNotFoundException,
    NotOwnedError, InvalidEmojiIdException
)
from src.schemas.mood_tracker import MoodTracker, MoodTrackerDateRequestAdd, MoodTrackerCreate
from src.services.base import BaseService
from src.services.emoji import EmojiService
from src.models import MoodTrackerOrm

class MoodTrackerService(BaseService):
    MIN_SCORE = 0
    MAX_SCORE = 100
    MIN_EMOJI_ID = 1
    MAX_EMOJI_ID = 10

    def _validate_score(self, score: int):
        if not (self.MIN_SCORE <= score <= self.MAX_SCORE):
            raise ScoreOutOfRangeError()

    def _validate_emojis(self, emoji_ids: List[int]):
        if not emoji_ids:
            raise InvalidEmojiIdException

        for eid in emoji_ids:
            if not (self.MIN_EMOJI_ID <= eid <= self.MAX_EMOJI_ID):
                raise InvalidEmojiIdException

    async def save_mood_tracker(self, data: MoodTrackerDateRequestAdd, user_id: uuid.UUID):
        self._validate_score(data.score)
        self._validate_emojis(data.emoji_ids)

        created_at = data.day or datetime.now()

        mood_tracker = MoodTrackerCreate(
            id=uuid.uuid4(),
            score=data.score,
            created_at=created_at,
            user_id=user_id,
            emoji_ids=data.emoji_ids
        )

        await self.db.mood_tracker.add(mood_tracker)
        await self.db.commit()

    async def get_mood_tracker(self, day: Optional[str], user_id: uuid.UUID) -> List[MoodTracker]:
        if day:
            target_date = datetime.strptime(day, "%Y-%m-%d").date()
            records = await self.db.mood_tracker.get_filtered(
                func.date(self.db.mood_tracker.model.created_at) == target_date,
                user_id=user_id
            )
        else:
            records = await self.db.mood_tracker.get_filtered(user_id=user_id)

        emoji_service = EmojiService(self.db)
        result = []
        for record in records:
            emoji_texts = []
            for eid in record.emoji_ids:
                emoji = await emoji_service.get_emoji_by_id(eid)
                if emoji:
                    emoji_texts.append(emoji.text)
            result.append(MoodTracker(
                id=record.id,
                score=record.score,
                created_at=record.created_at,
                user_id=record.user_id,
                emoji_ids=record.emoji_ids,
                emoji_texts=emoji_texts
            ))
        return result

    async def get_mood_tracker_by_id(self, mood_tracker_id: uuid.UUID, user_id: uuid.UUID) -> MoodTracker:
        record = await self.db.mood_tracker.get_one(id=mood_tracker_id)
        if str(record.user_id) != str(user_id):
            raise NotOwnedError()

        emoji_service = EmojiService(self.db)
        emoji_texts = []
        for eid in record.emoji_ids:
            emoji = await emoji_service.get_emoji_by_id(eid)
            if emoji:
                emoji_texts.append(emoji.text)

        return MoodTracker(
            id=record.id,
            score=record.score,
            created_at=record.created_at,
            user_id=record.user_id,
            emoji_ids=record.emoji_ids,
            emoji_texts=emoji_texts
        )
