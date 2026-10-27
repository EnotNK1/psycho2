import asyncio
from logging.config import fileConfig
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool
from src.config import settings
from src.database import Base
import src.models  # noqa: F401 -- registers tables for Alembic

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata


def migrations(connection):
    context.configure(
        connection=connection, target_metadata=target_metadata, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()


async def online():
    engine = create_async_engine(settings.DB_URL, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(migrations)
    await engine.dispose()


if context.is_offline_mode():
    context.configure(
        url=settings.DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(online())
