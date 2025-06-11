import logging
import uuid
from typing import Optional, Any, Dict

from src.exceptions import InternalErrorHTTPException, ObjectNotFoundHTTPException, ObjectNotFoundException, \
    MyAppException, AccessDeniedHTTPException
from src.models.clients import TasksOrm
from src.schemas.psychologist import BecomePsychologistRequest, UpdatePsychologistRequest
from src.schemas.task import Task
from src.schemas.users import UpdateManagerRequest
from src.services.base import BaseService
logger = logging.getLogger(__name__)

class PsychologistService(BaseService):
    async def become_psychologist(self, user_id: uuid.UUID, data: BecomePsychologistRequest):
        try:
            user_update = {
                "username": data.username,
                "gender": data.gender,
                "birth_date": data.birth_date,
                "city": data.city,
                "description": data.description,
                "department": data.department,
                "online": data.online,
                "face_to_face": data.face_to_face,
                "role_id": 3  # роль психолога
            }
            await self.db.users.edit(UpdatePsychologistRequest(**user_update), exclude_unset=True, id=user_id)

            await self.db.commit()
            return {"status": "OK", "message": "Successfully became psychologist"}

        except ObjectNotFoundHTTPException:
            await self.db.rollback()
            raise
        except Exception:
            await self.db.rollback()
            raise InternalErrorHTTPException()

    async def get_psychologist(self, psychologist_id: uuid.UUID):
        try:
            psychologist = await self.db.users.get_filtered(id=psychologist_id, role_id=3)
            return psychologist
        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении психологов: {ex}")
            raise MyAppException()

    async def get_all_psychologists(self):
        try:
            psychologist = await self.db.users.get_filtered(role_id=3)
            return psychologist
        except ObjectNotFoundException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Ошибка при получении психологов: {ex}")
            raise MyAppException()


    async def create_task_for_clients(
            self,
            text: str,
            test_id: uuid.UUID,
            mentor_id: uuid.UUID,
            client_ids: Optional[list[uuid.UUID]] = None
    ):
        try:
            if not await self.db.application.is_user_manager(mentor_id):
                raise AccessDeniedHTTPException()

            if client_ids is None:
                relations = await self.db.clients.get_filtered(
                    mentor_id=mentor_id,
                    status=True
                )
                client_ids = [rel.client_id for rel in relations]

                if not client_ids:
                    raise ObjectNotFoundException

            invalid_clients = []
            for client_id in client_ids:
                relation = await self.db.clients.get_one_or_none(
                    client_id=client_id,
                    mentor_id=mentor_id,
                    status=True
                )
                if not relation:
                    invalid_clients.append(str(client_id))

            if invalid_clients:
                raise ObjectNotFoundException

            test_title = None
            if test_id:
                test = await self.db.tests.get_one(id=test_id)
                test_title = test.title if test else None

            created_tasks = []
            for client_id in client_ids:
                task_id = uuid.uuid4()
                task = TasksOrm(
                    id=task_id,
                    text=text,
                    test_title=test_title,
                    test_id=test_id,
                    mentor_id=mentor_id,
                    client_id=client_id,
                    is_complete=False
                )
                self.db.session.add(task)
                created_tasks.append(task)

            await self.db.session.commit()

            return [
                Task(
                    id=task.id,
                    text=task.text,
                    test_title=task.test_title,
                    test_id=task.test_id,
                    mentor_id=task.mentor_id,
                    client_id=task.client_id,
                    is_complete=task.is_complete
                )
                for task in created_tasks
            ]


        except ObjectNotFoundException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.session.rollback()
            logger.error(f"Ошибка создания задач: {str(e)}")
            raise MyAppException()

    async def get_client_test_results(
            self,
            client_id: uuid.UUID,
            psychologist_id: uuid.UUID
    ) -> list[Dict[str, Any]]:
        try:
            # Проверяем, что клиент является подопечным данного психолога
            relation = await self.db.clients.get_one_or_none(
                client_id=client_id,
                mentor_id=psychologist_id,
                status=True
            )
            if not relation:
                raise ObjectNotFoundException(
                    f"Клиент с ID {client_id} не найден или не является вашим подопечным"
                )

            # Получаем все результаты тестов клиента
            test_results = await self.db.test_result.get_filtered(user_id=client_id)

            # Если результатов нет, возвращаем пустой список
            if not test_results:
                return []

            results = []

            # Для каждого результата теста собираем полную информацию
            for tr in test_results:
                try:
                    # Получаем результаты шкал для данного результата теста
                    scale_results = await self.db.scale_result.get_filtered(test_result_id=tr.id)

                    # Формируем структуру результата теста
                    result = {
                        "test_id": str(tr.test_id),
                        "test_result_id": str(tr.id),
                        "datetime": tr.date.isoformat(),
                        "scale_results": [],
                    }

                    # Для каждого результата шкалы получаем дополнительные данные
                    for sr in scale_results:
                        try:
                            # Получаем информацию о шкале
                            scale = await self.db.scales.get_one(id=sr.scale_id)
                            if not scale:
                                logger.warning(f"Шкала с ID {sr.scale_id} не найдена, пропускаем")
                                continue

                            borders = await self.db.borders.get_filtered(scale_id=scale.id)

                            conclusion = ""
                            color = ""
                            user_recommendation = ""
                            for border in borders:
                                if border.left_border <= sr.score <= border.right_border:
                                    conclusion = border.title
                                    color = border.color
                                    user_recommendation = border.user_recommendation
                                    break

                            # Добавляем результат шкалы
                            result["scale_results"].append({
                                "scale_id": str(scale.id),
                                "scale_title": scale.title,
                                "score": sr.score,
                                "max_score": scale.max,
                                "conclusion": conclusion,
                                "color": color,
                                "user_recommendation": user_recommendation,
                            })
                        except Exception as e:
                            logger.error(f"Ошибка обработки результата шкалы {sr.id}: {str(e)}")
                            continue

                    results.append(result)
                except Exception as e:
                    logger.error(f"Ошибка обработки результата теста {tr.id}: {str(e)}")
                    continue

            return results

        except ObjectNotFoundException:
            raise
        except Exception as ex:
            logger.error(f"Ошибка при получении результатов тестов клиента: {ex}", exc_info=True)
            raise MyAppException("Произошла ошибка при получении результатов тестов")