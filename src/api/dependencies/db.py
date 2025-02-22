from typing import Annotated
from fastapi import Depends

from src.utils.db_manager import DBManager
from src.database import async_session_maker


def get_db_manager():
    return DBManager(session_factory=async_session_maker)


async def get_db():
    async with get_db_manager() as db:
        yield db


DBDep = Annotated[DBManager, Depends(get_db)]
