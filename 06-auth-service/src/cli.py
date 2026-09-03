"""
python -m src.cli --login admin --password secret
"""

import asyncio

import typer
from sqlalchemy import select

from src.core.config import settings
from src.db.base import Base
from src.models.entity import User

app = typer.Typer()


async def create_superuser(login: str, password: str) -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    engine = create_async_engine(str(settings.pg_dsn))
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        # на всякий случай, если таблиц езе нет
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        stmt = select(User).where(User.login == login)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.role = "admin"
            typer.echo(f"Пользователь '{login}' обновлён до admin.")
        else:
            user = User(
                login=login, password=password, first_name="Admin", last_name="Admin"
            )
            user.role = "admin"
            session.add(user)
            typer.echo(f"Суперпользователь '{login}' создан.")

        await session.commit()

    await engine.dispose()


@app.command()
def createsuperuser(
    login: str = typer.Option(..., help="Логин суперпользователя"),
    password: str = typer.Option(None, help="Пароль (будет запрошен, если не указан)"),
) -> None:
    """Создать суперпользователя (role=admin)."""
    if password is None:
        password = typer.prompt("Пароль", hide_input=True)
    asyncio.run(create_superuser(login, password))


if __name__ == "__main__":
    app()
