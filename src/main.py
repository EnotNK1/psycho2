from fastapi import FastAPI
import logging
import sys
from pathlib import Path

from src.database import engine, Base

sys.path.append(str(Path(__file__).parent.parent))
from contextlib import asynccontextmanager
from fastapi.openapi.docs import get_swagger_ui_html
import uvicorn

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from src.api.auth import router as router_auth
from src.api.review import router as router_review
from src.api.diary import router as router_diary
from src.api.mood_tracker import router as router_mood_tracker

from src.init import redis_manager

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_manager.connect()
    FastAPICache.init(RedisBackend(redis_manager.redis), prefix="fastapi-cache")
    logging.info("FastAPI cache initialized")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logging.info("Database tables created")

    yield
    await redis_manager.close()


app = FastAPI(lifespan=lifespan)

app.include_router(router_auth)
app.include_router(router_review)
app.include_router(router_diary)
app.include_router(router_mood_tracker)


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
