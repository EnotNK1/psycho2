import json
import logging
import uuid
from typing import List, Type

from src.exceptions import ObjectNotFoundException, MyAppException, ObjectAlreadyExistsException
from src.models.education import EducationProgressOrm, educationThemeOrm
from src.schemas.education_material import (
    EducationThemeResponse,
    EducationMaterialResponse,
    CardResponse,
    EducationProgressResponse, CompleteEducation, EducationThemeAdd, EducationMaterialAdd, CardAdd,
    GetUserEducationProgressResponse
)
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class EducationService(BaseService):
    async def auto_create_education(self):
        try:
            with open("services/info/education_themes.json", encoding="utf-8") as file:
                themes_data = json.load(file)
            await self._add_themes(themes_data)

            with open("services/info/education_materials.json", encoding="utf-8") as file:
                materials_data = json.load(file)
            await self._add_materials(materials_data)

            with open("services/info/education_cards.json", encoding="utf-8") as file:
                cards_data = json.load(file)
            await self._add_cards(cards_data)

            await self.db.commit()
            return {"status": "OK", "message": "Образовательные материалы успешно созданы"}

        except Exception as ex:
            logger.error(f"Ошибка при создании образовательных материалов: {ex}")
            await self.db.rollback()
            raise MyAppException()

    async def _add_themes(self, themes_data):
        themes_data = [EducationThemeAdd.model_validate(theme) for theme in themes_data]
        for theme in themes_data:
            try:
                existing_theme = await self.db.education_theme.get_one_or_none(id=theme.id)
                if existing_theme:
                    logger.info(f"Тема {theme.theme} уже существует. Пропускаем.")
                else:
                    await self.db.education_theme.add(theme)
                    logger.info(f"Тема с id={theme.id} добавлена.")
            except Exception as ex:
                logger.error(f"Ошибка при добавлении теста: {ex}")
                await self.db.rollback()
                raise MyAppException()

    async def _add_materials(self, materials_data):
        try:
            validated_materials = [EducationMaterialAdd.model_validate(m) for m in materials_data]
            for material in validated_materials:
                existing = await self.db.education_material.get_one_or_none(id=material.id)
                if existing:
                    logger.info(f"Материал {material.id} уже существует. Пропускаем.")
                else:
                    await self.db.education_material.add(material)
                    logger.info(f"Материал {material.id} добавлен.")
        except Exception as ex:
            logger.error(f"Ошибка при добавлении материалов: {ex}")
            await self.db.rollback()
            raise MyAppException()

    async def _add_cards(self, cards_data):
        try:
            validated_cards = [CardAdd.model_validate(card) for card in cards_data]
            for card in validated_cards:
                existing = await self.db.education_card.get_one_or_none(id=card.id)
                if existing:
                    logger.info(f"Карточка {card.id} уже существует. Пропускаем.")
                else:
                    await self.db.education_card.add(card)
                    logger.info(f"Карточка {card.id} добавлена.")
        except Exception as ex:
            logger.error(f"Ошибка при добавлении карточек: {ex}")
            await self.db.rollback()
            raise MyAppException()

    async def get_all_education_themes(self) -> List[educationThemeOrm]:
        try:
            themes = await self.db.education_theme.get_all_with_materials_and_cards()
            return themes
        except ObjectNotFoundException:
            raise
        except Exception as ex:
            logger.error(f"Error in get_all_education_themes: {ex}")
            raise MyAppException()

    async def get_education_theme_materials(self, theme_id: uuid.UUID) -> List[EducationMaterialResponse]:
        try:
            # Получаем тему с материалами и карточками одним запросом
            theme = await self.db.education_theme.get_with_materials(theme_id)
            if not theme:
                raise ObjectNotFoundException(f"Theme with id {theme_id} not found")

            # Преобразуем материалы и вложенные карточки в схемы
            materials_response = []
            for material in theme.education_materials:
                cards_response = [
                    CardResponse(
                        id=card.id,
                        text=card.text,
                        number=card.number,
                        link_to_picture=card.link_to_picture
                    )
                    for card in getattr(material, "cards", [])
                ]

                materials_response.append(
                    EducationMaterialResponse(
                        id=material.id,
                        type=material.type,
                        number=material.number,
                        title=material.title,
                        link_to_picture=material.link_to_picture,
                        subtitle=material.subtitle,
                        cards=cards_response
                    )
                )
            return materials_response

        except ObjectNotFoundException:
            raise
        except Exception as ex:
            logger.error(f"Error in get_education_theme_materials: {ex}")
            raise MyAppException()

    async def complete_education_material(self, payload: CompleteEducation, user_id: uuid.UUID):
        try:

            material = await self.db.education_material.get_one_or_none(id=payload.education_material_id)
            if not material:
                raise ObjectNotFoundException

            existing_progress = await self.db.education_progress.get_one_or_none(
                user_id=user_id,
                education_material_id=payload.education_material_id
            )
            if existing_progress:

                raise ObjectAlreadyExistsException

            progress_entity = EducationProgressResponse(
                id=uuid.uuid4(),
                user_id=user_id,
                education_material_id=payload.education_material_id
            )
            await self.db.education_progress.add(progress_entity)
            await self.db.commit()

            logger.info(f"Пользователь {user_id} успешно завершил материал {payload.education_material_id}.")
        except ObjectNotFoundException:
            raise
        except ObjectAlreadyExistsException:
            raise
        except Exception as ex:
            await self.db.rollback()
            raise MyAppException()

    async def get_user_progress(self, user_id: uuid.UUID) -> List[GetUserEducationProgressResponse]:
        try:
            progress_entries = await self.db.education_progress.get_filtered(user_id=user_id)

            return [
                GetUserEducationProgressResponse(
                    user_id=entry.user_id,
                    education_material_id=entry.education_material_id
                )
                for entry in progress_entries
            ]
        except Exception as ex:
            logger.error(f"Ошибка при получении прогресса пользователя {user_id}: {ex}")
            raise MyAppException()