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
    GetUserEducationProgressResponse, EducationThemeWithMaterialsResponse, ThemeRecommendationResponse
)
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class EducationService(BaseService):
    async def auto_create_education(self):
        try:
            # Сначала удаляем все существующие данные
            await self._delete_all_education_data()

            # Затем добавляем новые данные
            with open("src/services/info/education_themes.json", encoding="utf-8") as file:
                themes_data = json.load(file)
            await self._add_themes(themes_data)

            with open("src/services/info/education_materials.json", encoding="utf-8") as file:
                materials_data = json.load(file)
            await self._add_materials(materials_data)

            with open("src/services/info/education_cards.json", encoding="utf-8") as file:
                cards_data = json.load(file)
            await self._add_cards(cards_data)

            await self.db.commit()
            return {"status": "OK", "message": "Образовательные материалы успешно перезаписаны"}

        except Exception as ex:
            logger.error(
                f"Ошибка при перезаписи образовательных материалов: {ex}")
            await self.db.rollback()
            raise MyAppException()

    async def _delete_all_education_data(self):
        """Удаляет все образовательные данные"""
        from sqlalchemy import text

        try:
            # Удаляем карточки
            await self.db.execute(text("DELETE FROM education_card"))
            # Удаляем материалы
            await self.db.execute(text("DELETE FROM education_material"))
            # Удаляем темы
            await self.db.execute(text("DELETE FROM education_theme"))
            logger.info("Все старые образовательные данные удалены")
        except Exception as e:
            logger.error(f"Ошибка при удалении данных: {e}")
            raise

    async def _add_themes(self, themes_data):
        themes = [EducationThemeAdd.model_validate(
            theme) for theme in themes_data]
        new_count = 0
        for theme in themes:
            existing = await self.db.education_theme.get_one_or_none(id=theme.id)
            if not existing:
                await self.db.education_theme.add(theme)
                new_count += 1
        if new_count:
            logger.info(f"{new_count} новых тем добавлено в базу.")
        else:
            logger.info("Все темы уже существуют в базе.")

    async def _add_materials(self, materials_data):
        materials = [EducationMaterialAdd.model_validate(
            m) for m in materials_data]
        new_count = 0
        for material in materials:
            existing = await self.db.education_material.get_one_or_none(id=material.id)
            if not existing:
                await self.db.education_material.add(material)
                new_count += 1
        if new_count:
            logger.info(f"{new_count} новых материалов добавлено в базу.")
        else:
            logger.info("Все материалы уже существуют в базе.")

    async def _add_cards(self, cards_data):
        cards = [CardAdd.model_validate(card) for card in cards_data]
        new_count = 0
        for card in cards:
            existing = await self.db.education_card.get_one_or_none(id=card.id)
            if not existing:
                await self.db.education_card.add(card)
                new_count += 1
        if new_count:
            logger.info(f"{new_count} новых карточек добавлено в базу.")
        else:
            logger.info("Все карточки уже существуют в базе.")

    async def get_all_education_themes(self) -> List[educationThemeOrm]:
        try:
            themes = await self.db.education_theme.get_all_with_materials_and_cards()
            return themes
        except ObjectNotFoundException:
            raise
        except Exception as ex:
            logger.error(f"Error in get_all_education_themes: {ex}")
            raise MyAppException()

    async def get_education_theme_materials(self, theme_id: uuid.UUID) -> EducationThemeWithMaterialsResponse:
        try:
            theme = await self.db.education_theme.get_with_materials(theme_id)
            if not theme:
                raise ObjectNotFoundException(
                    f"Theme with id {theme_id} not found")

            recommendations = []
            if theme.related_topics:
                for topic_id in theme.related_topics:
                    try:
                        # Используем новый метод без маппера
                        topic = await self.db.education_theme.get_orm_one_or_none(topic_id)

                        if topic:
                            recommendations.append(
                                ThemeRecommendationResponse(
                                    id=topic.id,
                                    theme=topic.theme,
                                    link=topic.link or "",
                                    tags=topic.tags
                                )
                            )
                    except Exception:
                        continue

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

            # Возвращаем полную информацию о теме с материалами
            return EducationThemeWithMaterialsResponse(
                id=theme.id,
                theme=theme.theme,
                link=theme.link or "",
                recommendations=recommendations,
                education_materials=materials_response
            )

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

            logger.info(
                f"Пользователь {user_id} успешно завершил материал {payload.education_material_id}.")
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
            logger.error(
                f"Ошибка при получении прогресса пользователя {user_id}: {ex}")
            raise MyAppException()
