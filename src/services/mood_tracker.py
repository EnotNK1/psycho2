import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import func

from src.api.chat_bot import load_data
from src.ontology.wellbeing_onto.api import recommendations, RecommendationRequest, ScaleResult

from src.exceptions import (
    ScoreOutOfRangeError,
    ObjectNotFoundException,
    NotOwnedError, InvalidEmojiIdException
)
from src.schemas.daily_tasks import DailyTaskId
from src.schemas.mood_tracker import MoodTracker, MoodTrackerDateRequestAdd, MoodTrackerCreate
from src.schemas.ontology import OntologyEntry
from src.services.base import BaseService
from src.services.daily_tasks import DailyTaskService
from src.services.emoji import EmojiService
from src.services.gamification import GamificationService
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

        mood_tracker_id = uuid.uuid4()

        mood_tracker = MoodTrackerCreate(
            id=mood_tracker_id,
            score=data.score,
            created_at=created_at,
            user_id=user_id,
            emoji_ids=data.emoji_ids
        )

        daily_tasks = await DailyTaskService(self.db).get_daily_tasks(user_id)
        for task in daily_tasks:
            if task["type"] == 2:
                daily_task_id_data = DailyTaskId(daily_task_id=task["id"])
                await DailyTaskService(self.db).complete_daily_task(daily_task_id_data, user_id)

        await self.db.mood_tracker.add(mood_tracker)

        gamification_service = GamificationService(self.db)
        await gamification_service.add_points_for_activity(user_id, "mood_tracker_used")

        scale_res_for_ontology = [ScaleResult(scale_title="Mood", score=data.score)]
        payload = RecommendationRequest(test_id="Tracker", scale_results=scale_res_for_ontology)

        ontology_res = recommendations(payload)
        print(ontology_res)

        tests_data = load_data("src/services/info/test_info.json")
        themes_data = load_data("src/services/info/education_themes.json")
        exercise_data = load_data("src/services/info/exercise_info.json")

        tests_dict = {item["id"]: item.get("link", "") for item in tests_data}
        themes_dict = {item["id"]: item.get("link_to_picture", "") for item in themes_data}
        exercise_dict = {item["id"]: item.get("picture_link", "") for item in exercise_data}

        for rec in ontology_res:
            material_id = rec["material_id"]
            picture = None
            if material_id in tests_dict:
                picture = tests_dict[material_id]
            elif material_id in themes_dict:
                picture = themes_dict[material_id]
            elif material_id in exercise_dict:
                picture = exercise_dict[material_id]

            ontology_entry = OntologyEntry(
                id=uuid.uuid4(),
                type=rec["type"],
                created_at=datetime.now(),
                destination_id=material_id,
                destination_title="Трекер настроения",
                link_to_picture=picture,
                user_id=user_id
            )

            await self.db.ontology_entry.add(ontology_entry)

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

    async def get_weekly_mood_tracker(self, user_id: uuid.UUID) -> List[MoodTracker]:
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=6)

        records = await self.db.mood_tracker.get_filtered(
            self.db.mood_tracker.model.created_at >= week_ago,
            self.db.mood_tracker.model.created_at <= today,
            user_id=user_id
        )

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

    async def get_mood_tracker_by_period(
        self,
        user_id: uuid.UUID,
        start_date: str,
        end_date: str
    ) -> List[MoodTracker]:

        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        records = await self.db.mood_tracker.get_filtered(
            self.db.mood_tracker.model.created_at >= start,
            self.db.mood_tracker.model.created_at <= end,
            user_id=user_id
        )

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
