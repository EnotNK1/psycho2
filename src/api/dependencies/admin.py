from fastapi import Depends, HTTPException
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.services.auth import AuthService

async def verify_admin(
    user_id: UserIdDep,
    db: DBDep
):

    user = await AuthService(db).get_one_or_none_user(id=user_id)
    if not user or user.role_id != 0:
        raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения операции")
    return user_id

async def verify_hrd(
    user_id: UserIdDep,
    db: DBDep
):

    user = await AuthService(db).get_one_or_none_user(id=user_id)
    if not user or user.role_id != 4:
        raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения операции")
    return user_id

async def verify_hr(
    user_id: UserIdDep,
    db: DBDep
):

    user = await AuthService(db).get_one_or_none_user(id=user_id)
    if not user or user.role_id != 3:
        raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения операции")
    return user_id

AdminIdDep = Depends(verify_admin)
HRDIdDep = Depends(verify_hrd)
HRIdDep = Depends(verify_hr)
