import uuid
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, update, delete

from src.exceptions import (
    TextEmptyError,
    TextTooLongError,
    ObjectNotFoundException,
    InternalErrorHTTPException,
)
from src.schemas.diary import AbcDiaryAdd, AbcDiaryUpdate, AbcDiary
from src.services.base import BaseService
from src.models.diary import AbcDiaryEntryOrm

logger = logging.getLogger(__name__)


class AbcDiaryService(BaseService):
    MAX_TEXT_LENGTH = 5000
    DEFAULT_PER_PAGE = 10

    def _validate_text(self, text: str) -> None:
        if not text or not text.strip():
            raise TextEmptyError("Текст не может быть пустым")
        if len(text) > self.MAX_TEXT_LENGTH:
            raise TextTooLongError(
                f"Максимальная длина текста - {self.MAX_TEXT_LENGTH} символов"
            )

    def _validate_entry_ownership(self, entry: AbcDiaryEntryOrm, user_id: uuid.UUID) -> None:
        # Приводим к строке для безопасного сравнения
        if str(entry.user_id) != str(user_id):
            raise ObjectNotFoundException("Запись не найдена")

    # ---- Создание записи ----
    async def create_entry(self, data: AbcDiaryAdd, user_id: uuid.UUID) -> AbcDiary:
        try:
            self._validate_text(data.activating_event)
            self._validate_text(data.beliefs)
            self._validate_text(data.consequences)

            now = datetime.now()
            orm_entry = AbcDiaryEntryOrm(
                id=uuid.uuid4(),
                user_id=user_id,
                activating_event=data.activating_event,
                beliefs=data.beliefs,
                consequences=data.consequences,
                created_at=now,
                updated_at=now,
            )
            self.db.session.add(orm_entry)
            await self.db.session.commit()
            await self.db.session.refresh(orm_entry)
            return AbcDiary.model_validate(orm_entry)

        except (TextEmptyError, TextTooLongError):
            raise
        except Exception as e:
            logger.error(f"Ошибка создания записи ABC-дневника: {str(e)}")
            await self.db.session.rollback()
            raise InternalErrorHTTPException()

    # ---- Получение списка записей пользователя (с пагинацией) ----
    async def get_user_entries(
        self, user_id: uuid.UUID, page: int = 1, per_page: Optional[int] = None
    ) -> List[AbcDiary]:
        try:
            if per_page is None:
                per_page = self.DEFAULT_PER_PAGE
            if per_page < 1:
                per_page = self.DEFAULT_PER_PAGE
            offset = (page - 1) * per_page

            stmt = (
                select(AbcDiaryEntryOrm)
                .where(AbcDiaryEntryOrm.user_id == user_id)
                .order_by(AbcDiaryEntryOrm.created_at.desc())
                .offset(offset)
                .limit(per_page)
            )
            result = await self.db.session.execute(stmt)
            entries = result.scalars().all()
            return [AbcDiary.model_validate(e) for e in entries]

        except Exception as e:
            logger.error(f"Ошибка получения записей пользователя: {str(e)}")
            raise InternalErrorHTTPException()

    # ---- Получение одной записи ----
    async def get_entry(self, entry_id: uuid.UUID, user_id: uuid.UUID) -> AbcDiary:
        try:
            print("перед селект")
            stmt = select(AbcDiaryEntryOrm).where(AbcDiaryEntryOrm.id == entry_id)
            result = await self.db.session.execute(stmt)
            entry = result.scalar_one_or_none()
            print("перед нот энтри")
            if not entry:
                raise ObjectNotFoundException("Запись не найдена")
            print("после нот энтри")
            self._validate_entry_ownership(entry, user_id)
            print("перед ретерн")
            return AbcDiary(
                id=entry.id,
                user_id=entry.user_id,
                activating_event=entry.activating_event,
                beliefs=entry.beliefs,
                consequences=entry.consequences,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
            )
        except ObjectNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Ошибка получения записи {entry_id}: {str(e)}")
            raise InternalErrorHTTPException()

    # ---- Обновление записи ----
    async def update_entry(
        self, entry_id: uuid.UUID, user_id: uuid.UUID, data: AbcDiaryUpdate
    ) -> AbcDiary:
        try:
            # Сначала получаем запись, чтобы проверить владельца
            stmt = select(AbcDiaryEntryOrm).where(AbcDiaryEntryOrm.id == entry_id)
            result = await self.db.session.execute(stmt)
            entry = result.scalar_one_or_none()
            if not entry:
                raise ObjectNotFoundException("Запись не найдена")
            self._validate_entry_ownership(entry, user_id)

            update_data = {}
            if data.activating_event is not None:
                self._validate_text(data.activating_event)
                update_data["activating_event"] = data.activating_event
            if data.beliefs is not None:
                self._validate_text(data.beliefs)
                update_data["beliefs"] = data.beliefs
            if data.consequences is not None:
                self._validate_text(data.consequences)
                update_data["consequences"] = data.consequences

            if not update_data:
                # Если ничего не обновляем, возвращаем текущую запись
                return AbcDiary.model_validate(entry)

            update_data["updated_at"] = datetime.now()

            # Выполняем обновление
            stmt = (
                update(AbcDiaryEntryOrm)
                .where(AbcDiaryEntryOrm.id == entry_id)
                .values(**update_data)
                .returning(AbcDiaryEntryOrm)
            )
            result = await self.db.session.execute(stmt)
            updated_entry = result.scalar_one()
            await self.db.session.commit()

            return AbcDiary.model_validate(updated_entry)

        except (ObjectNotFoundException, TextEmptyError, TextTooLongError):
            raise
        except Exception as e:
            logger.error(f"Ошибка обновления записи {entry_id}: {str(e)}")
            await self.db.session.rollback()
            raise InternalErrorHTTPException()

    # ---- Удаление записи ----
    async def delete_entry(self, entry_id: uuid.UUID, user_id: uuid.UUID) -> None:
        try:
            # Проверяем существование и владельца
            stmt = select(AbcDiaryEntryOrm).where(AbcDiaryEntryOrm.id == entry_id)
            result = await self.db.session.execute(stmt)
            entry = result.scalar_one_or_none()
            if not entry:
                raise ObjectNotFoundException("Запись не найдена")
            self._validate_entry_ownership(entry, user_id)

            # Удаляем
            stmt = delete(AbcDiaryEntryOrm).where(AbcDiaryEntryOrm.id == entry_id)
            await self.db.session.execute(stmt)
            await self.db.session.commit()
        except ObjectNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Ошибка удаления записи {entry_id}: {str(e)}")
            await self.db.session.rollback()
            raise InternalErrorHTTPException()

    # ---- Для психолога (записи клиента) ----
    async def get_client_entries(
        self,
        client_id: uuid.UUID,
        psychologist_id: uuid.UUID,
        page: int = 1,
        per_page: Optional[int] = None,
    ) -> List[AbcDiary]:
        try:
            if per_page is None:
                per_page = self.DEFAULT_PER_PAGE
            if per_page < 1:
                per_page = self.DEFAULT_PER_PAGE
            offset = (page - 1) * per_page

            # Проверка связи клиент-психолог (предположим, есть репозиторий clients)
            relation = await self.db.clients.get_one_or_none(
                client_id=client_id,
                mentor_id=psychologist_id,
                status=True,
            )
            if not relation:
                raise ObjectNotFoundException(
                    f"Клиент с ID {client_id} не найден или не является вашим подопечным"
                )

            stmt = (
                select(AbcDiaryEntryOrm)
                .where(AbcDiaryEntryOrm.user_id == client_id)
                .order_by(AbcDiaryEntryOrm.created_at.desc())
                .offset(offset)
                .limit(per_page)
            )
            result = await self.db.session.execute(stmt)
            entries = result.scalars().all()
            return [AbcDiary.model_validate(e) for e in entries]

        except ObjectNotFoundException:
            raise
        except Exception as e:
            logger.error(
                f"Ошибка получения записей клиента {client_id} психологом {psychologist_id}: {str(e)}"
            )
            raise InternalErrorHTTPException()

    # ---- Для администратора (все записи) ----
    async def get_all_entries(
        self, page: int = 1, per_page: Optional[int] = None
    ) -> List[AbcDiary]:
        try:
            if per_page is None:
                per_page = self.DEFAULT_PER_PAGE
            if per_page < 1:
                per_page = self.DEFAULT_PER_PAGE
            offset = (page - 1) * per_page

            stmt = (
                select(AbcDiaryEntryOrm)
                .order_by(AbcDiaryEntryOrm.created_at.desc())
                .offset(offset)
                .limit(per_page)
            )
            result = await self.db.session.execute(stmt)
            entries = result.scalars().all()
            return [AbcDiary.model_validate(e) for e in entries]

        except Exception as e:
            logger.error(f"Ошибка получения всех записей: {str(e)}")
            raise InternalErrorHTTPException()