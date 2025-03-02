from src.models.review import ReviewOrm
from src.repositories.mappers.mappers import ReviewDataMapper
from src.repositories.base import BaseRepository


class ReviewRepository(BaseRepository):
    model = ReviewOrm
    mapper = ReviewDataMapper
