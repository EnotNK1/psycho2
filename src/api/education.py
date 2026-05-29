import logging
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse

from src.api.dependencies.db import DBDep
from src.api.dependencies.user_id import UserIdDep
from src.exceptions import ObjectNotFoundHTTPException, MyAppHTTPException, ObjectNotFoundException, \
    ObjectAlreadyExistsException, ObjectAlreadyExistsHTTPException
from src.services.education import EducationService
from src.schemas.education_material import (
    EducationThemeResponse,
    EducationMaterialResponse,
    EducationProgressResponse,
    CompleteEducation, GetUserEducationProgressResponse, EducationThemeWithMaterialsResponse, CompleteEducationTheme,
    EducationThemeCreate, EducationThemeUpdate, CardCreate, CardUpdate, CardResponse,
    EducationMaterialCreate, EducationMaterialUpdate
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/education", tags=["Образовательные материалы"])
images_router = APIRouter(prefix="/images", tags=["Изображения"])


@router.post("/auto-create", summary="Автоматическое создание материалов")
async def auto_create_education(db: DBDep):
    try:
        return await EducationService(db).auto_create_education()
    except Exception as e:
        logger.error(f"Error in auto_create_education: {str(e)}")
        raise MyAppHTTPException


@router.post("/themes", response_model=EducationThemeResponse)
async def create_theme(theme_data: EducationThemeCreate, db: DBDep):
    return await EducationService(db).create_theme(theme_data)


@router.patch("/themes/{theme_id}", response_model=EducationThemeResponse)
async def update_theme(theme_id: uuid.UUID, theme_data: EducationThemeUpdate, db: DBDep):
    try:
        return await EducationService(db).update_theme(theme_id, theme_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.delete("/themes/{theme_id}", status_code=204)
async def delete_theme(theme_id: uuid.UUID, db: DBDep):
    try:
        await EducationService(db).delete_theme(theme_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.post("/themes/{theme_id}/materials", response_model=EducationMaterialResponse)
async def create_material(theme_id: uuid.UUID, material_data: EducationMaterialCreate, db: DBDep):
    try:
        return await EducationService(db).create_material(theme_id, material_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.patch("/materials/{material_id}", response_model=EducationMaterialResponse)
async def update_material(material_id: uuid.UUID, material_data: EducationMaterialUpdate, db: DBDep):
    try:
        return await EducationService(db).update_material(material_id, material_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.delete("/materials/{material_id}", status_code=204)
async def delete_material(material_id: uuid.UUID, db: DBDep):
    try:
        await EducationService(db).delete_material(material_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.post("/materials/{material_id}/cards", response_model=CardResponse)
async def create_card(material_id: uuid.UUID, card_data: CardCreate, db: DBDep):
    try:
        return await EducationService(db).create_card(material_id, card_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.patch("/cards/{card_id}", response_model=CardResponse)
async def update_card(card_id: uuid.UUID, card_data: CardUpdate, db: DBDep):
    try:
        return await EducationService(db).update_card(card_id, card_data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.delete("/cards/{card_id}", status_code=204)
async def delete_card(card_id: uuid.UUID, db: DBDep):
    try:
        await EducationService(db).delete_card(card_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException


@router.get("/themes/all")
async def get_all_education_themes(db: DBDep) -> List[EducationThemeResponse]:
    themes = await EducationService(db).get_all_education_themes()
    return themes


@router.get("/themes/{theme_id}/materials/list", summary="Материалы темы")
async def get_education_theme_materials(
    theme_id: uuid.UUID,
    db: DBDep,
    user_id: UserIdDep
) -> EducationThemeWithMaterialsResponse:
    try:
        return await EducationService(db).get_education_theme_materials(theme_id, user_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except Exception as e:
        logger.error(f"Error in get_education_theme_materials: {str(e)}")
        raise MyAppHTTPException


@router.post("/materials/complete", summary="Завершение материала")
async def complete_education_material(
    payload: CompleteEducation,
    db: DBDep,
    user_id: UserIdDep
):
    try:
        await EducationService(db).complete_education_material(payload, user_id)
        return {"status": "ok"}
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException
    except Exception as e:
        logger.error(f"Error in complete_education_material: {str(e)}")
        raise MyAppHTTPException

@router.post("/themes/complete", summary="Завершение темы")
async def complete_education_theme(
    payload: CompleteEducationTheme,
    db: DBDep,
    user_id: UserIdDep
):
    try:
        await EducationService(db).complete_education_theme(payload, user_id)
        return {"status": "ok"}
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException
    except Exception as e:
        logger.error(f"Error in complete_education_material: {str(e)}")
        raise MyAppHTTPException


@router.get("/progress", summary="Прогресс пользователя")
async def get_user_progress(
    db: DBDep,
    user_id: UserIdDep
) -> List[GetUserEducationProgressResponse]:
    try:
        return await EducationService(db).get_user_progress(user_id)
    except Exception as e:
        logger.error(f"Error in get_user_progress: {str(e)}")
        raise MyAppHTTPException
