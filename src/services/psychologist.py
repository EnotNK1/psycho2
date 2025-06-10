import logging
import uuid

from src.exceptions import InternalErrorHTTPException, ObjectNotFoundHTTPException, ObjectNotFoundException, \
    MyAppException
from src.schemas.psychologist import BecomePsychologistRequest, UpdatePsychologistRequest
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