import logging
import uuid
from typing import List
from src.exceptions import ObjectNotFoundException, MyAppException, ObjectAlreadyExistsException
from src.models.education import CardOrm, educationMaterialOrm, educationThemeOrm
from src.schemas.daily_tasks import DailyTaskId
from src.schemas.education_material import (
    EducationThemeResponse,
    EducationMaterialResponse,
    CardResponse,
    EducationProgressResponse, CompleteEducation, EducationThemeAdd, EducationMaterialAdd, CardAdd,
    GetUserEducationProgressResponse, EducationThemeWithMaterialsResponse, ThemeRecommendationResponse,
    CompleteEducationTheme, EducationThemeCreate, EducationThemeUpdate, EducationMaterialCreate,
    EducationMaterialUpdate, CardCreate, CardUpdate
)
from src.services.base import BaseService
from src.services.daily_tasks import DailyTaskService
from src.services.fixtures.education import EDUCATION
from src.services.gamification import GamificationService

logger = logging.getLogger(__name__)


class EducationService(BaseService):
    async def create_theme(self, data: EducationThemeCreate) -> EducationThemeResponse:
        theme = EducationThemeAdd(id=uuid.uuid4(), **data.model_dump())
        created = await self.db.education_theme.add(theme)
        await self.db.commit()
        return EducationThemeResponse.model_validate(created)

    async def update_theme(
        self, theme_id: uuid.UUID, data: EducationThemeUpdate
    ) -> EducationThemeResponse:
        existing = await self.db.education_theme.get_one_or_none(id=theme_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.education_theme.edit(data, exclude_unset=True, id=theme_id)
        await self.db.commit()
        updated = await self.db.education_theme.get_one(id=theme_id)
        return EducationThemeResponse.model_validate(updated)

    async def delete_theme(self, theme_id: uuid.UUID) -> None:
        if not await self.db.education_theme.get_one_or_none(id=theme_id):
            raise ObjectNotFoundException()
        await self.db.education_theme.delete(id=theme_id)

    async def create_material(
        self, theme_id: uuid.UUID, data: EducationMaterialCreate
    ) -> EducationMaterialResponse:
        if not await self.db.education_theme.get_one_or_none(id=theme_id):
            raise ObjectNotFoundException()
        material = EducationMaterialAdd(
            id=uuid.uuid4(),
            education_theme_id=theme_id,
            **data.model_dump(),
        )
        created = await self.db.education_material.add(material)
        await self.db.commit()
        return EducationMaterialResponse.model_validate(created)

    async def update_material(
        self, material_id: uuid.UUID, data: EducationMaterialUpdate
    ) -> EducationMaterialResponse:
        existing = await self.db.education_material.get_one_or_none(id=material_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.education_material.edit(data, exclude_unset=True, id=material_id)
        await self.db.commit()
        updated = await self.db.education_material.get_one(id=material_id)
        return EducationMaterialResponse.model_validate(updated)

    async def delete_material(self, material_id: uuid.UUID) -> None:
        if not await self.db.education_material.get_one_or_none(id=material_id):
            raise ObjectNotFoundException()
        await self.db.education_material.delete(id=material_id)

    async def create_card(
        self, material_id: uuid.UUID, data: CardCreate
    ) -> CardResponse:
        if not await self.db.education_material.get_one_or_none(id=material_id):
            raise ObjectNotFoundException()
        card = CardAdd(
            id=uuid.uuid4(),
            education_material_id=material_id,
            **data.model_dump(),
        )
        created = await self.db.education_card.add(card)
        await self.db.commit()
        return CardResponse.model_validate(created)

    async def update_card(self, card_id: uuid.UUID, data: CardUpdate) -> CardResponse:
        existing = await self.db.education_card.get_one_or_none(id=card_id)
        if not existing:
            raise ObjectNotFoundException()
        await self.db.education_card.edit(data, exclude_unset=True, id=card_id)
        await self.db.commit()
        updated = await self.db.education_card.get_one(id=card_id)
        return CardResponse.model_validate(updated)

    async def delete_card(self, card_id: uuid.UUID) -> None:
        if not await self.db.education_card.get_one_or_none(id=card_id):
            raise ObjectNotFoundException()
        await self.db.education_card.delete(id=card_id)

    async def auto_create_education(self):
        try:
            await self.seed_education()
            await self.db.commit()
            return {
                "status": "OK",
                "message": "Education content synchronized",
            }
        except Exception as ex:
            logger.error(f"Education synchronization failed: {ex}")
            await self.db.rollback()
            raise MyAppException()

    async def seed_education(self):
        for theme_data in EDUCATION:
            theme_id = uuid.UUID(theme_data["id"])
            theme = await self.db.education_theme.get_orm_one_or_none(theme_id)
            if theme is None:
                theme = educationThemeOrm(id=theme_id)
                await self.db.education_theme.add_entity(theme)

            theme.theme = theme_data["theme"]
            theme.link = theme_data["link"]
            theme.link_to_picture = theme_data.get("link_to_picture")
            theme.tags = theme_data.get("tags")
            theme.related_topics = theme_data.get("related_topics")

            fixture_material_ids = set()
            for material_data in theme_data.get("materials", []):
                material_id = uuid.UUID(material_data["id"])
                fixture_material_ids.add(material_id)
                material = await self.db.education_material.get_orm_one_or_none(
                    material_id
                )
                if material is None:
                    material = educationMaterialOrm(id=material_id)
                    await self.db.education_material.add_entity(material)

                material.type = material_data["type"]
                material.number = material_data["number"]
                material.title = material_data.get("title")
                material.link_to_picture = material_data.get("link_to_picture")
                material.subtitle = material_data.get("subtitle")
                material.education_theme_id = theme_id

                fixture_card_ids = set()
                for card_data in material_data.get("cards", []):
                    card_id = uuid.UUID(card_data["id"])
                    fixture_card_ids.add(card_id)
                    card = await self.db.education_card.get_orm_one_or_none(card_id)
                    if card is None:
                        card = CardOrm(id=card_id)
                        await self.db.education_card.add_entity(card)

                    card.text = card_data["text"]
                    card.number = card_data["number"]
                    card.link_to_picture = card_data.get("link_to_picture")
                    card.education_material_id = material_id

                await self.db.education_card.delete_not_in(
                    material_id,
                    fixture_card_ids,
                )

            await self.db.education_material.delete_not_in(
                theme_id,
                fixture_material_ids,
            )

        await self.db.education_theme.flush()

    async def get_all_education_themes(self) -> List[educationThemeOrm]:
        try:
            themes = await self.db.education_theme.get_all_with_materials_and_cards()
            return themes
        except ObjectNotFoundException:
            raise
        except Exception as ex:
            logger.error(f"Error in get_all_education_themes: {ex}")
            raise MyAppException()

    async def get_education_theme_materials(self, theme_id: uuid.UUID, user_id: uuid.UUID) -> EducationThemeWithMaterialsResponse:
        try:
            theme = await self.db.education_theme.get_with_materials(theme_id)
            if not theme:
                raise ObjectNotFoundException(f"Theme with id {theme_id} not found")

            # Рекомендации
            recommendations = []
            if theme.related_topics:
                for topic_id in theme.related_topics:
                    topic = await self.db.education_theme.get_orm_one_or_none(topic_id)
                    if topic:
                        recommendations.append(
                            ThemeRecommendationResponse(
                                id=topic.id,
                                theme=topic.theme,
                                link=topic.link or "",
                                link_to_picture=topic.link_to_picture,
                                tags=topic.tags
                            )
                        )

            # Материалы с карточками
            materials_response = []
            for material in theme.education_materials:
                cards_response = [
                    CardResponse(
                        id=card.id,
                        text=card.text,
                        number=card.number,
                        link_to_picture=card.link_to_picture
                    )
                    for card in material.cards
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

            ontology_temp = await self.db.ontology_entry.get_filtered(user_id=user_id)
            for temp in ontology_temp:
                if temp.destination_id == theme_id:
                    await self.db.ontology_entry.delete(user_id=user_id, destination_id=theme_id)

            return EducationThemeWithMaterialsResponse(
                id=theme.id,
                theme=theme.theme,
                link=theme.link or "",
                link_to_picture=theme.link_to_picture,
                recommendations=recommendations,
                education_materials=materials_response
            )

        except ObjectNotFoundException:
            raise
        except Exception as ex:
            logger.error(f"Error in get_education_theme_materials: {ex}")
            raise MyAppException()

    async def complete_education_theme(self, payload: CompleteEducationTheme, user_id: uuid.UUID):
        try:
            daily_tasks = await DailyTaskService(self.db).get_daily_tasks(user_id)
            for task in daily_tasks:
                if task["destination_id"] == payload.education_theme_id:
                    daily_task_id_data = DailyTaskId(daily_task_id=task["id"])
                    await DailyTaskService(self.db).complete_daily_task(daily_task_id_data, user_id)

        except ObjectNotFoundException:
            raise
        except ObjectAlreadyExistsException:
            raise
        except Exception as ex:
            await self.db.rollback()
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

            gamification_service = GamificationService(self.db)
            await gamification_service.add_points_for_activity(user_id, "theory_read")

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
