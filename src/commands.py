# src/commands.py
import asyncio
import uuid
import click
from datetime import date
from src.api.dependencies.db import get_db
from src.models.users import UsersOrm
from src.services.auth import AuthService


@click.group()
def cli():
    pass


@cli.command()
@click.argument('email')
@click.argument('password')
def create_admin(email, password):
    """Создание администратора: 'python -m src.commands create-admin admin@example.com password'     """

    async def run():
        async for db in get_db():
            try:
                existing_user = await db.users.get_one_or_none(email=email)
                if existing_user:
                    click.echo("Пользователь с таким email уже существует")
                    return

                auth_service = AuthService(db)

                hashed_password = auth_service.hash_password(password)

                admin_user = UsersOrm(
                    id=uuid.uuid4(),
                    username="admin",
                    email=email,
                    hashed_password=hashed_password,
                    city="",
                    gender="male",
                    is_active=True,
                    role_id=0,
                    company="",
                    online=True,
                    birth_date=date.today(),
                    phone_number="",
                    description="",
                    department="",
                    job_title="",
                    face_to_face=True
                )

                db.session.add(admin_user)
                await db.session.commit()

                click.echo(f"Администратор {email} успешно создан!")
                click.echo(f"Логин: {email}")
                click.echo(f"Пароль: {password}")

            except Exception as e:
                await db.session.rollback()
                click.echo(f"Ошибка: {str(e)}")
                import traceback
                click.echo(f"Детали ошибки: {traceback.format_exc()}")

    asyncio.run(run())


if __name__ == '__main__':
    cli()