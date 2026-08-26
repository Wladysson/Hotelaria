from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from src.core.config import settings
from src.models.base import Base
from src.models.permission import Permission
from src.models.role import Role
from src.models.user import User


config = context.config


if config.config_file_name is not None:
    fileConfig(
        config.config_file_name
    )


target_metadata = Base.metadata


def get_database_url() -> str:
    return settings.database_url.replace(
        "+asyncpg",
        "",
    )


def run_migrations_offline() -> None:
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(
        config.config_ini_section
    )

    configuration[
        "sqlalchemy.url"
    ] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()