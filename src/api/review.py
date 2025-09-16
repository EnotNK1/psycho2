import uuid

from fastapi import APIRouter

from src.schemas.review import ReviewRequestAdd
from src.services.auth import AuthService
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.services.review import ReviewService

router = APIRouter(prefix="/review", tags=["Отзывы пользователей"])


@router.get("")
async def get_reviews(
    db: DBDep,
    user_id: UserIdDep,
):
    return await ReviewService(db).get_reviews()


@router.post("")
async def create_review(db: DBDep, user_id: UserIdDep, data: ReviewRequestAdd):
    await ReviewService(db).add_review(data, user_id)
    return {"status": "OK"}


@router.patch("/{review_id}")
async def read_review(db: DBDep, user_id: UserIdDep, review_id: uuid.UUID):
    await ReviewService(db).read_review(review_id=review_id)
    return {"status": "OK"}


@router.delete("/{review_id}")
async def delete_review(db: DBDep, user_id: UserIdDep, review_id: uuid.UUID):
    await ReviewService(db).delete_review(review_id=review_id)
    return {"status": "OK"}
