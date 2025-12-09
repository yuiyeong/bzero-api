"""Fix alembic version to 442b2cf6617e (0007)"""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from bzero.core.settings import Environment, get_settings


async def fix_alembic_version():
    import os

    os.environ["ENVIRONMENT"] = "test"

    settings = get_settings()
    if settings.environment != Environment.TEST:
        raise RuntimeError("TEST 환경에서만 실행 가능합니다")

    engine = create_async_engine(settings.database.async_url)

    async with engine.begin() as conn:
        # Update alembic_version to 0007
        await conn.execute(
            text("UPDATE alembic_version SET version_num = '442b2cf6617e'")
        )

    await engine.dispose()
    print("✅ Alembic version updated to 442b2cf6617e (0007)")


if __name__ == "__main__":
    asyncio.run(fix_alembic_version())
