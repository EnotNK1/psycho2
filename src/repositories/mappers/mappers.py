from src.repositories.mappers.base import DataMapper
from src.schemas.users import User
from src.schemas.review import Review
from src.models.users import UsersOrm
from src.models.review import ReviewOrm


class UserDataMapper(DataMapper):
    db_model = UsersOrm
    schema = User


class ReviewDataMapper(DataMapper):
    db_model = ReviewOrm
    schema = Review
