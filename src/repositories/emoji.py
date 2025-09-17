import json
from typing import List

from src.models import EmojiOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import EmojiDataMapper
from src.schemas.emoji import Emoji


class EmojiRepository(BaseRepository):
    model = EmojiOrm
    mapper = EmojiDataMapper

    async def load_emojis_to_db(self):
        with open("services/info/emojis.json", encoding="utf-8") as file:
            raw_data = json.load(file)

        emojis: List[Emoji] = [Emoji.model_validate(item) for item in raw_data]

        await self.add_bulk(emojis)
