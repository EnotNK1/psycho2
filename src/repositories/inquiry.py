import json
from typing import List

from src.models import InquiryOrm

from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import InquiryDataMapper
from src.schemas.inquiry import Inquiry


class InquiryRepository(BaseRepository):
    model = InquiryOrm
    mapper = InquiryDataMapper

    async def load_inquiries_to_db(self):
        with open("services/info/inquiry.json", encoding="utf-8") as file:
            raw_data = json.load(file)

        inquiries: List[Inquiry] = [Inquiry.model_validate(item) for item in raw_data]

        await self.add_bulk(inquiries)