import logging

from src.schemas.inquiry import Inquiry
from src.services.base import BaseService

logger = logging.getLogger(__name__)

class InquiryService(BaseService):
    async def create(self, inquiry_data: dict):
        await self.db.inquiry.add(Inquiry(**inquiry_data))

    async def check_and_create_inquiries(self, inquiry_data):
        for inquiry in inquiry_data:
            existing_inquiry = await self.db.inquiry.get_one_or_none(id=inquiry['id'])
            if existing_inquiry:
                logger.info(f"Inquiry с id={inquiry['id']} уже существует. Пропускаем.")
            else:
                await self.create(inquiry)
                logger.info(f"Inquiry с id={inquiry['id']} создан.")
