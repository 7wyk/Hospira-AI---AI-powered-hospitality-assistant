from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.database import Base
from app.config import get_settings
from app import models  # noqa: F401
config = context.config
settings = get_settings()
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata
def get_database_url():
    url = settings.database_url
    return (
        url.replace("+asyncpg", "+psycopg")
        .replace("+aiosqlite", "")
    )
def run_migrations_offline():
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
def run_migrations_online():
    section = config.get_section(
        config.config_ini_section,
        {},
    )
    section["sqlalchemy.url"] = get_database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

