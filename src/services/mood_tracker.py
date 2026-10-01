import uuid
import logging
from collections import defaultdict
from datetime import datetime, time, timedelta
from typing import Optional, List
from zoneinfo import ZoneInfo

from sqlalchemy import func

from src.api.chat_bot import load_data
from src.ontology.wellbeing_onto.api import recommendations, RecommendationRequest, ScaleResult

from src.exceptions import (
    ScoreOutOfRangeError,
    InvalidDateFormatError,
    ObjectNotFoundException,
    NotOwnedError, InvalidEmojiIdException
)
from src.schemas.daily_tasks import DailyTaskId
from src.schemas.mood_tracker import (
    MoodTracker,
    MoodTrackerCreate,
    MoodTrackerDateRequestAdd,
    MoodEmotionCatalog,
    MoodEmotionGroup,
    MoodInfluenceCategory,
    MoodInfluenceOption,
    WeeklyMoodTrackerDay,
)
from src.schemas.ontology import OntologyEntry
from src.services.base import BaseService
from src.services.daily_tasks import DailyTaskService
from src.services.emoji import EmojiService
from src.services.fixtures.exercise import EXERCISES
from src.services.gamification import GamificationService
from src.models import MoodTrackerOrm


APP_TIMEZONE = ZoneInfo("Asia/Tomsk")
logger = logging.getLogger(__name__)

MOOD_PRIMARY_EMOTIONS = [
    "Печаль",
    "Злость",
    "Страх",
    "Радость",
    "Вина",
    "Интерес",
    "Спокойствие",
]

MOOD_ADDITIONAL_EMOTIONS = [
    "Грусть",
    "Одиночество",
    "Разочарование",
    "Беспомощность",
    "Тоска",
    "Апатия",
    "Гнев",
    "Злость",
    "Раздражение",
    "Обида",
    "Фрустрация (когда что-то не получается)",
    "Возмущение",
    "Ненависть",
    "Тревога",
    "Паника",
    "Ужас",
    "Неуверенность в себе",
    "Напряжение",
    "Стресс",
    "Удовлетворение",
    "Вдохновение",
    "Благодарность",
    "Умиротворение",
    "Расслабленность",
    "Стыд",
    "Смущение",
    "Чувство неадекватности",
    "Удивление",
    "Любопытство",
    "Озадаченность",
    "Воодушевление",
    "Равнодушие",
]

MOOD_EMOTION_CATALOG = MoodEmotionCatalog(
    groups=[
        MoodEmotionGroup(
            id="primary",
            title="Основные",
            emotions=MOOD_PRIMARY_EMOTIONS,
        ),
        MoodEmotionGroup(
            id="additional",
            title="Дополнительные",
            emotions=MOOD_ADDITIONAL_EMOTIONS,
        ),
    ],
    allow_custom_text=True,
    custom_title="Другое",
)

MOOD_EMOTIONS = MOOD_PRIMARY_EMOTIONS + [
    emotion
    for emotion in MOOD_ADDITIONAL_EMOTIONS
    if emotion not in MOOD_PRIMARY_EMOTIONS
]

MOOD_INFLUENCE_CATEGORIES = [
    MoodInfluenceCategory(
        id="contacts",
        title="Контакты",
        options=[
            MoodInfluenceOption(id="family", title="Семья"),
            MoodInfluenceOption(id="friends", title="Друзья"),
            MoodInfluenceOption(id="partner", title="Партнер"),
            MoodInfluenceOption(id="colleagues", title="Коллеги"),
            MoodInfluenceOption(id="pets", title="Питомцы"),
            MoodInfluenceOption(id="clients", title="Клиенты"),
        ],
    ),
    MoodInfluenceCategory(
        id="activities",
        title="Занятия",
        options=[
            MoodInfluenceOption(id="study", title="Учеба"),
            MoodInfluenceOption(id="sex", title="Секс"),
            MoodInfluenceOption(id="work", title="Работа"),
            MoodInfluenceOption(id="hobby", title="Хобби"),
            MoodInfluenceOption(id="household", title="Быт"),
            MoodInfluenceOption(id="walk", title="Прогулка"),
            MoodInfluenceOption(id="reading", title="Чтение"),
            MoodInfluenceOption(id="cinema", title="Кино"),
        ],
    ),
    MoodInfluenceCategory(
        id="general_health",
        title="Общее здоровье",
        options=[
            MoodInfluenceOption(id="bad_sleep", title="Плохой сон"),
            MoodInfluenceOption(id="sport", title="Спорт"),
            MoodInfluenceOption(id="illness", title="Болезнь"),
            MoodInfluenceOption(id="good_sleep", title="Хороший сон"),
            MoodInfluenceOption(id="hunger", title="Голод"),
            MoodInfluenceOption(id="overeating", title="Переедание"),
            MoodInfluenceOption(id="balanced_food", title="Сбалансированная еда"),
            MoodInfluenceOption(id="smoking", title="Курение"),
            MoodInfluenceOption(id="alcohol", title="Алкоголь"),
        ],
    ),
    MoodInfluenceCategory(
        id="female_health",
        title="Женское здоровье",
        options=[
            MoodInfluenceOption(id="menstrual_phase", title="Менструальная фаза"),
            MoodInfluenceOption(id="follicular_phase", title="Фолликулярная фаза"),
            MoodInfluenceOption(id="ovulatory_phase", title="Овуляторная фаза"),
            MoodInfluenceOption(id="luteal_phase", title="Лютеиновая фаза"),
        ],
    ),
    MoodInfluenceCategory(
        id="other",
        title="Другое",
        allow_custom_text=True,
        options=[],
    ),
]


def local_now() -> datetime:

    return datetime.now(APP_TIMEZONE).replace(tzinfo=None)


class MoodTrackerService(BaseService):
    MIN_SCORE = 0
    MAX_SCORE = 100
    MIN_EMOJI_ID = 1
    MAX_EMOJI_ID = 10

    def _load_info_data(self, path: str) -> list[dict]:
        try:
            return load_data(path)
        except FileNotFoundError:
            logger.warning("Info file %s not found, using empty list", path)
            return []

    def _load_exercise_recommendation_data(self) -> list[dict]:
        return [
            {
                "id": item["id"],
                "title": item.get("title", ""),
                "picture_link": item.get("picture_link", ""),
            }
            for item in EXERCISES
        ]

    def _validate_score(self, score: int):
        if not (self.MIN_SCORE <= score <= self.MAX_SCORE):
            raise ScoreOutOfRangeError()

    def _validate_emojis(self, emoji_ids: List[int]):
        if not emoji_ids:
            raise InvalidEmojiIdException

        for eid in emoji_ids:
            if not (self.MIN_EMOJI_ID <= eid <= self.MAX_EMOJI_ID):
                raise InvalidEmojiIdException

    def _validate_mood_details(self, data: MoodTrackerDateRequestAdd):
        other_emotion = data.other_emotion.strip() if data.other_emotion else None
        if not data.emoji_ids and not data.emotions and not other_emotion:
            raise ValueError("At least one emotion is required")

        valid_emotions = set(MOOD_EMOTIONS)
        invalid_emotions = [emotion for emotion in data.emotions if emotion not in valid_emotions]
        if invalid_emotions:
            raise ValueError(f"Unknown emotions: {', '.join(invalid_emotions)}")

        categories = {category.id: category for category in MOOD_INFLUENCE_CATEGORIES}
        for factor in data.influence_factors:
            category = categories.get(factor.category_id)
            if category is None:
                raise ValueError(f"Unknown influence category: {factor.category_id}")

            valid_option_ids = {option.id for option in category.options}
            invalid_option_ids = [
                option_id
                for option_id in factor.option_ids
                if option_id not in valid_option_ids
            ]
            if invalid_option_ids:
                raise ValueError(
                    f"Unknown influence options for {factor.category_id}: "
                    + ", ".join(invalid_option_ids)
                )

            if factor.custom_text and not category.allow_custom_text:
                raise ValueError(f"Custom text is not allowed for {factor.category_id}")

            if category.allow_custom_text and not factor.custom_text:
                raise ValueError(f"Custom text is required for {factor.category_id}")

    def _build_emotions_for_storage(self, data: MoodTrackerDateRequestAdd) -> list[str]:
        emotions = list(data.emotions)
        other_emotion = data.other_emotion.strip() if data.other_emotion else None
        if other_emotion:
            emotions.append(other_emotion)
        return emotions

    async def save_mood_tracker(self, data: MoodTrackerDateRequestAdd, user_id: uuid.UUID):
        self._validate_score(data.score)
        if data.emoji_ids:
            self._validate_emojis(data.emoji_ids)
        self._validate_mood_details(data)
        emotions = self._build_emotions_for_storage(data)

        created_at = (
            datetime.combine(data.day, time.min)
            if data.day
            else local_now()
        )

        mood_tracker_id = uuid.uuid4()

        mood_tracker = MoodTrackerCreate(
            id=mood_tracker_id,
            score=data.score,
            created_at=created_at,
            user_id=user_id,
            emoji_ids=data.emoji_ids,
            emotions=emotions,
            influence_factors=data.influence_factors,
        )

        daily_tasks = await DailyTaskService(self.db).get_daily_tasks(user_id)
        for task in daily_tasks:
            if task["type"] == 2:
                daily_task_id_data = DailyTaskId(daily_task_id=task["id"])
                await DailyTaskService(self.db).complete_daily_task(daily_task_id_data, user_id)

        await self.db.mood_tracker.add(mood_tracker)

        gamification_service = GamificationService(self.db)
        await gamification_service.add_points_for_activity(user_id, "mood_tracker_used")

        scale_res_for_ontology = [ScaleResult(scale_title="Настроение", score=data.score)]
        payload = RecommendationRequest(test_id="Tracker", scale_results=scale_res_for_ontology)

        ontology_res = recommendations(payload)
        logger.debug("Mood tracker ontology recommendations: %s", ontology_res)

        tests_data = self._load_info_data("src/services/info/test_info.json")
        themes_data = self._load_info_data("src/services/info/education_themes.json")
        exercise_data = self._load_exercise_recommendation_data()

        tests_dict = {
            item["id"]: {
                "link": item.get("link", ""),
                "destination_title": item.get("title", "")
            }
            for item in tests_data
        }

        themes_dict = {
            item["id"]: {
                "link": item.get("link_to_picture", ""),
                "destination_title": item.get("theme", "")
            }
            for item in themes_data
        }

        exercise_dict = {
            item["id"]: {
                "link": item.get("picture_link", ""),
                "destination_title": item.get("title", "")
            }
            for item in exercise_data
        }

        for rec in ontology_res:
            material_id = rec["material_id"]
            picture = None
            destination_title = None
            if material_id in tests_dict:
                picture = tests_dict[material_id]["link"]
                destination_title = tests_dict[material_id]["destination_title"]
            elif material_id in themes_dict:
                picture = themes_dict[material_id]["link"]
                destination_title = themes_dict[material_id]["destination_title"]
            elif material_id in exercise_dict:
                picture = exercise_dict[material_id]["link"]
                destination_title = exercise_dict[material_id]["destination_title"]

            ontology_entry = OntologyEntry(
                id=uuid.uuid4(),
                type=rec["type"],
                created_at=local_now(),
                destination_id=material_id,
                destination_title=destination_title,
                link_to_picture=picture,
                user_id=user_id
            )

            await self.db.ontology_entry.add(ontology_entry)

        await self.db.commit()

    async def get_mood_tracker(self, day: Optional[str], user_id: uuid.UUID) -> List[MoodTracker]:
        if day:
            try:
                target_date = datetime.strptime(day, "%Y-%m-%d").date()
            except ValueError:
                raise InvalidDateFormatError()
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
            for eid in record.emoji_ids or []:
                emoji = await emoji_service.get_emoji_by_id(eid)
                if emoji:
                    emoji_texts.append(emoji.text)
            result.append(MoodTracker(
                id=record.id,
                score=record.score,
                created_at=record.created_at,
                user_id=record.user_id,
                emoji_ids=record.emoji_ids or [],
                emoji_texts=emoji_texts,
                emotions=getattr(record, "emotions", None) or [],
                influence_factors=getattr(record, "influence_factors", None) or [],
            ))
        return result

    async def get_weekly_mood_tracker(
        self,
        user_id: uuid.UUID,
    ) -> List[WeeklyMoodTrackerDay]:
        today = local_now().date()
        week_start = today - timedelta(days=today.weekday())
        next_week_start = week_start + timedelta(days=7)
        period_start = datetime.combine(week_start, time.min)
        period_end = datetime.combine(next_week_start, time.min)

        records = await self.db.mood_tracker.get_filtered(
            self.db.mood_tracker.model.created_at >= period_start,
            self.db.mood_tracker.model.created_at < period_end,
            user_id=user_id
        )

        emoji_service = EmojiService(self.db)
        records_by_day = defaultdict(list)
        for record in sorted(records, key=lambda item: item.created_at):
            emoji_texts = []
            for eid in record.emoji_ids or []:
                emoji = await emoji_service.get_emoji_by_id(eid)
                if emoji:
                    emoji_texts.append(emoji.text)
            serialized_record = MoodTracker(
                id=record.id,
                score=record.score,
                created_at=record.created_at,
                user_id=record.user_id,
                emoji_ids=record.emoji_ids or [],
                emoji_texts=emoji_texts,
                emotions=getattr(record, "emotions", None) or [],
                influence_factors=getattr(record, "influence_factors", None) or [],
            )
            records_by_day[record.created_at.date()].append(serialized_record)

        return [
            WeeklyMoodTrackerDay(
                date=week_start + timedelta(days=offset),
                weekday=offset + 1,
                mood_trackers=records_by_day[week_start + timedelta(days=offset)],
            )
            for offset in range(7)
        ]

    async def get_mood_tracker_by_period(
        self,
        user_id: uuid.UUID,
        start_date: str,
        end_date: str
    ) -> List[MoodTracker]:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise InvalidDateFormatError()

        records = await self.db.mood_tracker.get_filtered(
            self.db.mood_tracker.model.created_at >= datetime.combine(start, time.min),
            self.db.mood_tracker.model.created_at < datetime.combine(
                end + timedelta(days=1),
                time.min,
            ),
            user_id=user_id
        )

        emoji_service = EmojiService(self.db)
        result = []
        for record in records:
            emoji_texts = []
            for eid in record.emoji_ids or []:
                emoji = await emoji_service.get_emoji_by_id(eid)
                if emoji:
                    emoji_texts.append(emoji.text)
            result.append(MoodTracker(
                id=record.id,
                score=record.score,
                created_at=record.created_at,
                user_id=record.user_id,
                emoji_ids=record.emoji_ids or [],
                emoji_texts=emoji_texts,
                emotions=getattr(record, "emotions", None) or [],
                influence_factors=getattr(record, "influence_factors", None) or [],
            ))
        return result

    async def get_mood_tracker_by_id(self, mood_tracker_id: uuid.UUID, user_id: uuid.UUID) -> MoodTracker:
        record = await self.db.mood_tracker.get_one(id=mood_tracker_id)
        if record is None:
            raise ObjectNotFoundException()
        if str(record.user_id) != str(user_id):
            raise NotOwnedError()

        emoji_service = EmojiService(self.db)
        emoji_texts = []
        for eid in record.emoji_ids or []:
            emoji = await emoji_service.get_emoji_by_id(eid)
            if emoji:
                emoji_texts.append(emoji.text)

        return MoodTracker(
            id=record.id,
            score=record.score,
            created_at=record.created_at,
            user_id=record.user_id,
            emoji_ids=record.emoji_ids or [],
            emoji_texts=emoji_texts,
            emotions=getattr(record, "emotions", None) or [],
            influence_factors=getattr(record, "influence_factors", None) or [],
        )
