from src.repositories.mappers.base import DataMapper
from src.schemas.users import User
from src.models.users import UsersOrm


class UserDataMapper(DataMapper):
    db_model = UsersOrm
    schema = User
