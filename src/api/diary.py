import uuid
from http.client import HTTPException
from fastapi import Query

from fastapi import APIRouter

from src.schemas.diary import DiaryRequestAdd, DiaryDateRequestAdd, DiaryCheckResponse
from src.api.dependencies.user_id import UserIdDep
from src.api.dependencies.db import DBDep
from src.services.diary import DiaryService
from datetime import date, datetime

router = APIRouter(prefix="/diary", tags=["Вольный дневник(Заметки)"])


@router.get("")
async def get_diary(
    db: DBDep,
    user_id: UserIdDep,
):
    return await DiaryService(db).get_diary()


@router.post("")
async def create_diary(db: DBDep, user_id: UserIdDep, data: DiaryRequestAdd):
    await DiaryService(db).add_diary(data, user_id)
    return {"status": "OK"}

@router.get("/with_date")
async def get_diary_by_day(db: DBDep, day: str):
    return await DiaryService(db).get_diary_by_day(day)


@router.post("/with_date")
async def create_diary_with_date(db: DBDep, user_id: UserIdDep, data: DiaryDateRequestAdd):
    await DiaryService(db).add_diary_with_date(data, user_id)
    return {"status": "OK"}


@router.get("/by_month")
async def check_diary_for_month(db: DBDep, timestamp: int = Query(..., title="Unix Timestamp", description="Unix Timestamp для проверки наличия заметок за месяц")):
    diary_info = await DiaryService(db).get_diary_for_month(timestamp)
    return diary_info

#
# @router.post("/writing_free_diary_with_date")
# async def writing_free_diary_with_date(db: DBDep, user_id: UserIdDep, data: FreeDiaryCreate):
#     await DiaryService(db).create_free_diary(user_id, data)
#     return {"status": "OK"}
#
#
# @router.get("/reading_free_diary_with_date", response_model=List[FreeDiaryResponse])
# async def reading_free_diary_with_date(db: DBDep, user_id: UserIdDep, date: datetime.date):
#     return await DiaryService(db).get_free_diary_by_date(user_id, date)
#
#
# @router.post("/writing_think_diary")
# async def writing_think_diary(db: DBDep, user_id: UserIdDep, data: DiaryRecordCreate):
#     await DiaryService(db).create_diary_record(user_id, data)
#     return {"status": "OK"}
#
#
# @router.get("/get_all_think_diary", response_model=List[DiaryRecordResponse])
# async def get_all_think_diary(db: DBDep, user_id: UserIdDep):
#     return await DiaryService(db).get_all_diary_records(user_id)
