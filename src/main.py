from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from contextlib import asynccontextmanager
from fastapi.openapi.docs import get_swagger_ui_html
import uvicorn

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from src.api.auth import router as router_auth
from src.api.tests import router as router_tests, images_router
from src.api.manager import router as router_manager
from src.api.application import router as application_router
from src.api.review import router as router_review
from src.api.diary import router as router_diary
from src.api.mood_tracker import router as router_mood_tracker
from src.api.client import router as router_client
from src.api.admin import router as router_admin
from src.api.education import router as router_education
from src.api.psychologist import router as router_psychologist
from src.api.daily_tasks import router as router_daily_tasks
from src.api.gamification import router as router_gamification
from src.api.exercise import router as router_exercise
from src.api.user_task import router as router_user_task
from src.api.yandex_auth import router as router_yandex_auth
from src.api.chat_bot import router as router_chat_bot

from src.init import redis_manager

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_manager.connect()
    FastAPICache.init(RedisBackend(redis_manager.redis), prefix="fastapi-cache")
    logging.info("FastAPI cache initialized")
    yield
    await redis_manager.    close()


app = FastAPI(lifespan=lifespan)

app.include_router(router_auth)
app.include_router(router_yandex_auth)
app.include_router(router_tests)
app.include_router(images_router)
app.include_router(router_manager)
app.include_router(application_router)
app.include_router(router_review)
app.include_router(router_diary)
app.include_router(router_mood_tracker)
app.include_router(router_client)
app.include_router(router_admin)
app.include_router(router_education)
app.include_router(router_psychologist)
app.include_router(router_daily_tasks)
app.include_router(router_gamification)
app.include_router(router_exercise)
app.include_router(router_user_task)
app.include_router(router_chat_bot)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True)
