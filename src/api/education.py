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
    CompleteEducation, GetUserEducationProgressResponse, EducationThemeWithMaterialsResponse, CompleteEducationTheme
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


@router.get("/themes/all")
async def get_all_education_themes(db: DBDep) -> List[EducationThemeResponse]:
    themes = await EducationService(db).get_all_education_themes()
    return themes


@router.get("/themes/{theme_id}/materials/list", summary="Материалы темы")
async def get_education_theme_materials(
    theme_id: uuid.UUID,
    db: DBDep
) -> EducationThemeWithMaterialsResponse:
    try:
        return await EducationService(db).get_education_theme_materials(theme_id)
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
