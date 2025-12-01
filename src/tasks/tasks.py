import asyncio

from email.mime.text import MIMEText
from pydantic import EmailStr
import smtplib

from src.database import async_session_maker_null_pool
from src.tasks.celery_app import celery_instance
from src.utils.db_manager import DBManager

from itsdangerous import URLSafeTimedSerializer
from src.services.auth import serializer


@celery_instance.task(name="send_email_to_users")
def send_email_to_recover_password(email: EmailStr):
    token = serializer.dumps(email)
    reset_link = f"https://одеяло.tech/password/change/{token}"

    subject = "Password Reset"
    message = f"Перейдите по ссылке для восстановления пароля: {reset_link}"
    send_email(email, subject, message)


def send_email(receiver_email: str, subject: str, message: str):
    sender_email = "athaethaet@mail.ru"
    password = "I2pGEnTYbGVtRVkLW1Qi"

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    server = smtplib.SMTP_SSL("smtp.mail.ru", 465)
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, msg.as_string())
    server.quit()
