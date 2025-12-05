"""
Alembic environment configuration for async SQLAlchemy.

This module configures Alembic to work with async SQLAlchemy, enabling database migrations with async database drivers like asyncpg.
"""

from logging.config import fileConfig
import asyncio

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import Base and all models for autogenerate support
from app.db.base import Base
from app.models import User
from app.core.config import settings

# Alembic Config objects provides access to .ini file values
config = context.config

# Override sqlalchemy.url with value from settings
# Allows using environment variables for database URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
# Sets up loggers for Alembic operations
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for 'autogenerate' support
# Tells Alembic about our models for automatic migration generation
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an Engine is acceptable here as well.
    By skipping the Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with the given connection.

    This is called by run_async_migrations with an async connection that's been converted to sync for Alembic's use.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """
    Run migrations in async mode.

    Creates an async engine and runs migrations within an async context.
    This is necessary when using async database drivers like asyncpg.
    """
    # Create async engine from config
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool, # Don't pool connections for migrations
    )

    # Run migrations in async context
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    
    # Dispose of engine
    await connectable.dispose()

def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection with the context.
    This is the standard mode for running migrations.
    """
    # Run async migrations using asyncio
    asyncio.run(run_async_migrations())

# Determine which mode to run in
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()