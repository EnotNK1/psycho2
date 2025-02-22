import asyncio

from src.database import async_session_maker_null_pool
from src.tasks.celery_app import celery_instance
from src.utils.db_manager import DBManager


# @celery_instance.task(name="send_emails_to_users")
# def send_emails_to_users():
#     asyncio.run(())
