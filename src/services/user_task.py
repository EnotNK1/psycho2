import uuid
from calendar import monthrange
from datetime import datetime, date, timedelta
from typing import Optional
from venv import logger

from sqlalchemy import func, false, select

from src.exceptions import (
    TextEmptyError,
    TextTooLongError,
    FutureDateError,
    InternalErrorHTTPException,
    InvalidDateFormatError,
    InvalidTimestampError, DateException
)
from src.models import UserTaskOrm
from src.schemas.diary import Diary, DiaryDateRequestAdd
from src.schemas.user_task import UserTaskRequestAdd, UserTask, UserTaskRequestUpdate, \
    UserTaskTextUpdate, UserTaskCompleteUpdate, UserTaskTextCompleteUpdate, UserTaskRequestDelete
from src.services.base import BaseService


class UserTaskService(BaseService):
    async def add_user_task(self, data: UserTaskRequestAdd, user_id: uuid.UUID):
        try:
            created_at = datetime.now()

            user_task = UserTask(
                id=uuid.uuid4(),
                text=data.text,
                created_at=created_at,
                is_complete=False,
                user_id=user_id
            )

            await self.db.user_task.add(user_task)
            await self.db.commit()

        except TextEmptyError:
            raise
        except TextTooLongError:
            raise
        except InvalidDateFormatError:
            raise
        except FutureDateError:
            raise
        except Exception as e:
            logger.error(f"Ошибка добавления записи: {str(e)}")
            raise InternalErrorHTTPException()

    async def update_user_task(self, data: UserTaskRequestUpdate):
        try:
            if data.is_complete is not None and data.text is not None:
                new_data = UserTaskTextCompleteUpdate(text=data.text, is_complete=data.is_complete)
            elif data.is_complete is None:
                new_data = UserTaskTextUpdate(text=data.text)
            else:
                new_data = UserTaskCompleteUpdate(is_complete=data.is_complete)

            await self.db.user_task.edit(
                data=new_data,
                exclude_unset=True,
                id=data.user_task_id
            )


            await self.db.commit()

        except TextEmptyError:
            raise
        except TextTooLongError:
            raise
        except InvalidDateFormatError:
            raise
        except FutureDateError:
            raise
        except Exception as e:
            logger.error(f"Ошибка добавления записи: {str(e)}")
            raise InternalErrorHTTPException()


    async def get_actual_user_tasks(self, user_id: uuid.UUID, selected_date: Optional[date] = None):

        try:
            incomplete_tasks = await self.db.user_task.get_filtered(
                user_id=user_id,
                is_complete=False
            )

            if selected_date:
                start_of_day = datetime.combine(selected_date, datetime.min.time())
                end_of_day = datetime.combine(selected_date, datetime.max.time())

                query = select(UserTaskOrm).where(
                    UserTaskOrm.user_id == user_id,
                    UserTaskOrm.created_at >= start_of_day,
                    UserTaskOrm.created_at <= end_of_day
                )

                result = await self.db.execute(query)
                daily_tasks = result.scalars().all()

                all_tasks = list({task.id: task for task in incomplete_tasks + daily_tasks}.values())
            else:
                all_tasks = incomplete_tasks

            tasks_json = []
            for task in all_tasks:
                tasks_json.append({
                    "id": str(task.id),
                    "text": task.text,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "is_complete": task.is_complete,
                    "user_id": str(task.user_id)
                })

            return tasks_json

        except Exception as e:
            print(f"Ошибка при получении задач: {e}")
            return []

    async def get_completed_user_tasks(
            self,
            user_id: uuid.UUID,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ):
        """
        Возвращает только выполненные задачи пользователя.

        Если даты переданы - задачи в границах дат.
        Если даты не переданы - задачи за последнюю неделю.
        """
        if (start_date and not end_date) or (end_date and not start_date):
            raise DateException
        try:
            if not end_date:
                end_date = datetime.now().date()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            start_date_only = start_datetime.date()
            end_date_only = end_datetime.date()

            start_of_day = datetime.combine(start_date_only, datetime.min.time())
            end_of_day = datetime.combine(end_date_only, datetime.max.time())

            print(f"Получено datetime: start={start_datetime}, end={end_datetime}")
            print(f"Поиск по дням: с {start_of_day} по {end_of_day}")

            # Создаем запрос для выполненных задач за период
            query = select(UserTaskOrm).where(
                UserTaskOrm.user_id == user_id,
                UserTaskOrm.is_complete == True,
                UserTaskOrm.created_at >= start_of_day,
                UserTaskOrm.created_at <= end_of_day
            ).order_by(UserTaskOrm.created_at.desc())

            # Выполняем запрос
            result = await self.db.execute(query)
            completed_tasks = result.scalars().all()

            # Сортируем задачи по дате создания (новые сначала)
            completed_tasks.sort(key=lambda x: x.created_at, reverse=True)

            # Преобразуем в JSON
            tasks_json = [
                {
                    "id": str(task.id),
                    "text": task.text,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "is_complete": task.is_complete,
                    "user_id": str(task.user_id)
                }
                for task in completed_tasks
            ]

            return tasks_json

        except Exception as e:
            print(f"Ошибка при получении выполненных задач: {e}")
            return []


    async def delete(self, data: UserTaskRequestDelete):
        try:
            await self.db.user_task.delete(id=data.user_task_id)
            await self.db.commit()

            return {"status": "OK"}

        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            raise InternalErrorHTTPException()
