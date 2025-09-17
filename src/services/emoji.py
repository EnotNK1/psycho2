import logging

from src.schemas.emoji import Emoji
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class EmojiService(BaseService):
    async def create(self, emoji_data: dict):
        await self.db.emoji.add(Emoji(**emoji_data))

    async def check_and_create_emojis(self, emoji_data):
        created = 0
        skipped = 0

        for emoji in emoji_data:
            existing_emoji = await self.db.emoji.get_one_or_none(id=emoji["id"])
            if existing_emoji:
                skipped += 1
            else:
                await self.create(emoji)
                created += 1

        if created > 0:
            logger.info(f"{created} emoji успешно созданы.")
        elif skipped > 0:
            logger.info("Все emoji уже существуют в базе.")
        else:
            logger.info("Файл emoji пустой, ничего не добавлено.")

    async def get_all_emojis(self):
        return await self.db.emoji.get_all()

    async def get_emoji_by_id(self, emoji_id: int):
        return await self.db.emoji.get_one_or_none(id=emoji_id)
