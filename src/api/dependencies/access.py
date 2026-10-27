from uuid import UUID
from fastapi import HTTPException
from src.enums import RoleEnum


async def require_client_access(db, viewer_id: UUID, client_id: UUID):
    viewer = await db.users.get_one_or_none(id=viewer_id)
    if viewer is None:
        raise HTTPException(401, "Требуется авторизация")
    if viewer_id == client_id or viewer.role_id == RoleEnum.ADMIN:
        return
    if viewer.role_id == RoleEnum.PSYCHOLOGIST:
        relation = await db.clients.get_one_or_none(
            client_id=client_id, mentor_id=viewer_id, status=True
        )
        if relation:
            return
    raise HTTPException(404, "Объект не найден")


async def require_psychologist(db, user_id: UUID):
    user = await db.users.get_one_or_none(id=user_id)
    if user is None or user.role_id != RoleEnum.PSYCHOLOGIST:
        raise HTTPException(403, "Доступ только психологу")
