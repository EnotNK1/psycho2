import logging
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.config import ROOT, settings
from src.database import engine
from src.api.auth import router as auth_router
from src.api.tests import router as tests_router
from src.api.psychologist import router as psychologist_router
from src.api.application import router as applications_router
from src.api.client import router as client_router
from src.api.yandex_auth import router as yandex_router
from src.exceptions import (
    MyAppException,
    ObjectNotFoundException,
    ObjectAlreadyExistsException,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("compas")


@asynccontextmanager
async def lifespan(app):
    yield
    await engine.dispose()


app = FastAPI(title="Compas API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
for router in (
    auth_router,
    yandex_router,
    tests_router,
    applications_router,
    client_router,
    psychologist_router,
):
    app.include_router(router)
app.mount("/images", StaticFiles(directory=ROOT / "src/images"), name="images")


@app.middleware("http")
async def request_metrics(request: Request, call_next):
    request_id = str(uuid4())
    started = perf_counter()
    response = await call_next(request)
    elapsed = perf_counter() - started
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Server-Timing"] = f"app;dur={elapsed * 1000:.2f}"
    # Do not log bodies, auth headers, passwords or actual private URL identifiers.
    route = request.scope.get("route")
    logger.info(
        "request id=%s method=%s route=%s status=%s seconds=%.3f",
        request_id,
        request.method,
        getattr(route, "path", "static"),
        response.status_code,
        elapsed,
    )
    return response


@app.exception_handler(MyAppException)
async def domain_error(request, error):
    status = (
        404
        if isinstance(error, ObjectNotFoundException)
        else 409
        if isinstance(error, ObjectAlreadyExistsException)
        else 400
    )
    return JSONResponse(
        {
            "detail": "Объект не найден"
            if status == 404
            else "Не удалось выполнить запрос"
        },
        status_code=status,
    )


@app.exception_handler(IntegrityError)
async def integrity_error(request, error):
    return JSONResponse({"detail": "Конфликт данных"}, status_code=409)


@app.get("/health/live", tags=["Состояние"])
async def live():
    return {"status": "ok"}


@app.get("/health/ready", tags=["Состояние"])
async def ready():
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return JSONResponse({"status": "unavailable"}, status_code=503)
