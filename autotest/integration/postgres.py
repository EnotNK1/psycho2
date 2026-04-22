import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def integration_db_url() -> str:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5433")
    user = os.getenv("DB_USER", "test")
    password = os.getenv("DB_PASS", "test")
    name = os.getenv("DB_NAME", "testdb")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


def create_integration_engine():
    return create_async_engine(integration_db_url(), future=True)


def create_session_factory(engine):
    return async_sessionmaker(bind=engine, expire_on_commit=False)


async def recreate_tables(engine, metadata, tables):
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(lambda sync_conn: metadata.create_all(sync_conn, tables=tables))


async def drop_test_schema(engine):
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
