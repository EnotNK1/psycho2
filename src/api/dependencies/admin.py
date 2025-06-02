from fastapi import Depends
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.services.auth import AuthService
from src.exceptions import InsufficientPermissionsHTTPException

async def verify_admin(
    user_id: UserIdDep,
    db: DBDep
):

    user = await AuthService(db).get_one_or_none_user(id=user_id)
    if not user or user.role_id != 0:
        raise InsufficientPermissionsHTTPException()
    return user_id

AdminIdDep = Depends(verify_admin)
