import uuid
import logging
import json
from pathlib import Path

from fastapi import HTTPException
from typing import List

from sqlalchemy import update, delete

from src.enums import DailyTaskType
from src.exceptions import ObjectNotFoundException, UserNotFoundException, InternalErrorHTTPException, ValidationError
from src.models import DailyTaskOrm
from src.schemas.daily_tasks import DailyTaskId
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class DailyTaskService(BaseService):

    async def get_daily_tasks(self, user_id: uuid.UUID) -> List:
        try:
            tasks = await self.db.daily_tasks.get_filtered(user_id=user_id, is_current=True)
            tasks_sorted = sorted(tasks, key=lambda x: x.number)
            task_list = []
            for t in tasks_sorted:
                task_list.append({
                    "id": t.id,
                    "title": t.title,
                    "short_description": t.short_desc,
                    "destination_id": t.destination_id,
                    "is_complete": t.is_complete,
                    "type": t.type,
                })
            return task_list
        except Exception as e:
            logger.error(f"Ошибка при получении ежедневных заданий: {e}")
            raise HTTPException(status_code=500, detail="Ошибка получения ежедневных заданий")

    async def set_last_day_tasks(self, user_id: uuid.UUID):
        try:
            tasks = await self.db.daily_tasks.get_filtered(user_id=user_id)
            for t in tasks:
                t.is_complete = False
                t.is_current = False
                if t.number in [25, 26, 27]:
                    t.is_current = True
                self.db.session.add(t)
            await self.db.session.commit()
        except Exception as e:
            await self.db.session.rollback()
            logger.error(f"Ошибка при установке последнего дня: {e}")
            raise

    async def complete_daily_task(self, payload: DailyTaskId, user_id: uuid.UUID) -> dict:
        try:
            result = await self.db.session.execute(
                update(DailyTaskOrm)
                .where(DailyTaskOrm.id == payload.daily_task_id)
                .where(DailyTaskOrm.user_id == user_id)
                .values(is_complete=True)
            )

            if result.rowcount == 0:
                raise ObjectNotFoundException("Задание не найдено")

            await self.db.session.commit()

            return {"status": "success", "message": "Задание отмечено как выполненное"}

        except Exception as e:
            await self.db.session.rollback()
            logger.error(f"Ошибка при выполнении задания: {e}")
            raise HTTPException(status_code=500, detail="Не удалось отметить задание как выполненное")

    def load_daily_tasks_from_json(self) -> List[dict]:
        try:
            json_path = Path("src/services/info/daily_tasks.json")

            if not json_path.exists():
                logger.error(f"Файл не найден: {json_path.absolute()}")
                raise ObjectNotFoundException("Файл daily_tasks.json не найден")

            with open(json_path, encoding="utf-8") as file:
                daily_tasks_data = json.load(file)

            if not isinstance(daily_tasks_data, list):
                raise json.JSONDecodeError("Ожидался список заданий")

            return daily_tasks_data

        except FileNotFoundError as ex:
            logger.error(f"Файл daily_tasks.json не найден: {ex}")
            raise ObjectNotFoundException("Файл с заданиями не найден")
        except json.JSONDecodeError as ex:
            logger.error(f"Ошибка парсинга JSON файла: {ex}")
            raise ValidationError("Ошибка формата файла с заданиями")
        except Exception as ex:
            logger.error(f"Неожиданная ошибка при загрузке заданий: {ex}")
            raise InternalErrorHTTPException()

    async def add_daily_tasks_for_new_user(self, user_id: uuid.UUID) -> dict:
        """Обновление ежедневных заданий с переносом и добавлением новых"""
        try:
            user = await self.db.users.get_one_or_none(id=user_id)
            if not user:
                raise UserNotFoundException(f"Пользователь с ID {user_id} не найден")

            daily_tasks_data = self.load_daily_tasks_from_json()

            first_day_tasks = sorted(
                [d for d in daily_tasks_data if d["day"] == 1],
                key=lambda d: d["number"]
            )
            for t_data in first_day_tasks:
                daily_task = DailyTaskOrm(
                    id=uuid.uuid4(),
                    title=t_data["title"],
                    short_desc=t_data["short_description"],
                    destination_id=uuid.UUID(t_data["destination_id"]),
                    number=t_data["number"],
                    day=t_data["day"],
                    is_complete=False,
                    is_current=True,
                    type=DailyTaskType[t_data["type"]],
                    user_id=user_id
                )
                self.db.session.add(daily_task)
            await self.db.session.commit()
            return {"status": "success", "message": "Назначены задания первого дня"}

        except Exception as ex:
            await self.db.session.rollback()
            logger.error(f"Ошибка при обновлении заданий: {ex}")
            raise InternalErrorHTTPException()

    async def refresh_daily_tasks(self, user_id: uuid.UUID) -> dict:
        try:
            user = await self.db.users.get_one_or_none(id=user_id)
            if not user:
                raise UserNotFoundException(f"Пользователь с ID {user_id} не найден")

            daily_tasks_data = self.load_daily_tasks_from_json()

            all_tasks_before = await self.db.daily_tasks.get_filtered(user_id=user_id)

            completed_tasks = await self.db.daily_tasks.get_filtered(
                user_id=user_id,
                is_complete=True
            )

            if completed_tasks:
                delete_stmt = delete(DailyTaskOrm).where(
                    DailyTaskOrm.user_id == user_id,
                    DailyTaskOrm.is_complete == True
                )
                await self.db.session.execute(delete_stmt)

            await self.db.session.commit()
            self.db.session.expire_all()

            unfinished_tasks: List[DailyTaskOrm] = await self.db.daily_tasks.get_filtered(
                user_id=user_id,
                is_complete=False
            )

            if not unfinished_tasks:
                last_day = max(d["day"] for d in daily_tasks_data)

                prev_day = max((t.day for t in all_tasks_before), default=0)

                next_day = prev_day + 1
                if next_day > last_day:
                    next_day = 1

                next_day_tasks = sorted(
                    [d for d in daily_tasks_data if d["day"] == next_day],
                    key=lambda d: d["number"]
                )

                for t_data in next_day_tasks:
                    daily_task = DailyTaskOrm(
                        id=uuid.uuid4(),
                        title=t_data["title"],
                        short_desc=t_data["short_description"],
                        destination_id=uuid.UUID(t_data["destination_id"]),
                        number=t_data["number"],
                        day=t_data["day"],
                        is_complete=False,
                        is_current=True,
                        type=DailyTaskType[t_data["type"]],
                        user_id=user_id
                    )
                    self.db.session.add(daily_task)

                await self.db.session.commit()
                return {"status": "success", "message": f"Назначены задания {next_day}-го дня"}

            current_day = max(t.day for t in unfinished_tasks)

            current_day_tasks = [t for t in unfinished_tasks if t.day == current_day]
            unfinished_count = len(current_day_tasks)

            for task in unfinished_tasks:
                task.is_current = False

            for task in unfinished_tasks:
                task.is_current = True

            tasks_to_add_count = 0
            if unfinished_count == 1:
                tasks_to_add_count = 3
            elif unfinished_count == 2:
                tasks_to_add_count = 2
            elif unfinished_count >= 3:
                tasks_to_add_count = 0

            next_day = current_day + 1

            next_day_tasks = sorted(
                [d for d in daily_tasks_data if d["day"] == next_day],
                key=lambda d: d["number"]
            )

            added_count = 0

            existing_task_keys = {(t.title, t.day, t.number) for t in unfinished_tasks}

            for t_data in next_day_tasks:
                if added_count >= tasks_to_add_count:
                    break

                task_key = (t_data["title"], t_data["day"], t_data["number"])

                if task_key not in existing_task_keys:
                    daily_task = DailyTaskOrm(
                        id=uuid.uuid4(),
                        title=t_data["title"],
                        short_desc=t_data["short_description"],
                        destination_id=uuid.UUID(t_data["destination_id"]),
                        number=t_data["number"],
                        day=t_data["day"],
                        is_complete=False,
                        is_current=True,
                        type=DailyTaskType[t_data["type"]],
                        user_id=user_id
                    )
                    self.db.session.add(daily_task)
                    added_count += 1
                    existing_task_keys.add(task_key)

            await self.db.session.commit()

            return {"status": "success", "message": "Ежедневные задания обновлены"}

        except Exception as ex:
            await self.db.session.rollback()
            logger.error(f"Ошибка при обновлении заданий: {ex}", exc_info=True)
            raise InternalErrorHTTPException()
