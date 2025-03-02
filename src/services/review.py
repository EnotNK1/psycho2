import uuid
from datetime import datetime

from src.schemas.review import ReviewRequestAdd, Review, ReviewRead
from src.services.base import BaseService


class ReviewService(BaseService):
    async def add_review(self, data: ReviewRequestAdd, user_id: uuid.UUID):
        user = await self.db.users.get_one_or_none(id=user_id)
        user_email = user.email
        review = Review(
            id=uuid.uuid4(),
            text=data.text,
            email=user_email,
            is_read=False,
            created_at=datetime.now(),
        )
        await self.db.review.add(review)
        await self.db.commit()

    async def get_reviews(self):
        return await self.db.review.get_all()

    async def read_review(self, review_id: uuid.UUID):
        data = ReviewRead(is_read=True)
        await self.db.review.edit(data, exclude_unset=True, id=review_id)
        await self.db.commit()

    async def delete_review(self, review_id: uuid.UUID):
        await self.db.review.delete(id=review_id)
        await self.db.commit()
