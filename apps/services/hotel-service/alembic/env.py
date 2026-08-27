from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.core.config import settings
from src.core.database import Base

# Importa os models para que o SQLAlchemy registre todas as tabelas.
from src.models.amenity import Amenity
from src.models.city import City
from src.models.hotel import Hotel
from src.models.image import Image
from src.models.room import Room
from src.models.room_type import RoomType


config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Retorna a URL do banco configurada para o serviço.
    """
    return settings.database_url


def run_migrations_offline() -> None:
    """
    Executa migrations sem estabelecer conexão com o banco.
    """
    database_url = get_database_url()

    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(
    connection: Connection,
) -> None:
    """
    Executa migrations utilizando uma conexão existente.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Executa migrations utilizando SQLAlchemy assíncrono.
    """
    configuration = config.get_section(
        config.config_ini_section,
        {},
    )

    configuration["sqlalchemy.url"] = (
        get_database_url()
    )

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            do_run_migrations
        )

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Executa migrations em modo online.
    """
    import asyncio

    asyncio.run(
        run_async_migrations()
    )


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()