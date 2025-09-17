import logging
from src.schemas.inquiry import Inquiry
from src.services.base import BaseService

logger = logging.getLogger(__name__)

class InquiryService(BaseService):
    async def create(self, inquiry_data: dict):
        await self.db.inquiry.add(Inquiry(**inquiry_data))

    async def check_and_create_inquiries(self, inquiry_data):
        created, skipped = 0, 0

        for inquiry in inquiry_data:
            existing_inquiry = await self.db.inquiry.get_one_or_none(id=inquiry['id'])
            if existing_inquiry:
                skipped += 1
            else:
                await self.create(inquiry)
                created += 1

        if created > 0:
            logger.info(f"{created} inquiry успешно создан(о).")
        elif skipped > 0:
            logger.info("Все inquiry уже существуют в базе.")
        else:
            logger.info("Файл inquiry пустой, ничего не добавлено.")
