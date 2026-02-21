import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import sys
import os
import importlib.util
import sysconfig

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_stdlib_platform():
    for base_dir in [sysconfig.get_path('stdlib'), sysconfig.get_path('platstdlib')]:
        if not base_dir:
            continue
        candidate = os.path.join(base_dir, 'platform.py')
        if os.path.isfile(candidate):
            spec = importlib.util.spec_from_file_location('platform', candidate)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    return None


_stdlib_platform = _load_stdlib_platform()

sys.modules.pop('platform', None)

from platform.api.database import Base
from platform.api.models import (
    Organization, Connector, Customer, CustomerFeatures,
    CustomerSegment, CustomerSegmentMembership, Campaign, Alert
)

if _stdlib_platform is not None:
    sys.modules['platform'] = _stdlib_platform

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    from platform.api.config import settings
    return settings.DATABASE_URL_SYNC


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine
    url = get_url().replace("postgresql://", "postgresql+asyncpg://")
    connectable = create_async_engine(url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
