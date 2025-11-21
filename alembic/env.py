from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context

from src.core.config import env_settings
from src.infrastructure.postgres.connection import Base

from src.infrastructure.postgres.models import *

DATABASE_URL = (
    f"postgresql://{env_settings.PG_USERNAME}:{env_settings.PG_PASSWORD}"
    f"@{env_settings.PG_HOST}:{env_settings.PG_PORT}/{env_settings.PG_DATABASE}"
)
config = context.config

config.set_main_option('sqlalchemy.url', DATABASE_URL)

fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(config.get_main_option("sqlalchemy.url"))

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
