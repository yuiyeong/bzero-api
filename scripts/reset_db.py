"""데이터베이스 리셋 및 시드 데이터 생성 스크립트

모든 테이블을 삭제하고 마이그레이션을 다시 적용한 후 시드 데이터를 생성합니다.

사용법:
    uv run python scripts/reset_db.py
"""

import asyncio
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bzero.core.settings import get_settings


# 시드 스크립트 실행 순서
SEED_SCRIPTS = [
    "seed_cities.py",
    "seed_airships.py",
    "seed_guest_houses.py",
    "seed_city_questions.py",
    "seed_conversation_cards.py",
]


async def drop_all_tables():
    """데이터베이스의 모든 테이블을 삭제합니다."""
    settings = get_settings()
    engine = create_async_engine(settings.database.async_url, echo=False)

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        # public 스키마의 모든 테이블 삭제 (CASCADE)
        await session.execute(text("DROP SCHEMA public CASCADE"))
        await session.execute(text("CREATE SCHEMA public"))
        await session.execute(text("GRANT ALL ON SCHEMA public TO public"))
        await session.commit()

    await engine.dispose()
    print("✓ 모든 테이블 삭제 완료")


def run_alembic_upgrade():
    """Alembic 마이그레이션을 실행합니다."""
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("✗ Alembic 마이그레이션 실패:")
        print(result.stderr)
        sys.exit(1)
    print("✓ Alembic 마이그레이션 완료")


def run_seed_script(script_name: str):
    """시드 스크립트를 실행합니다."""
    scripts_dir = Path(__file__).parent
    script_path = scripts_dir / script_name

    result = subprocess.run(
        ["uv", "run", "python", str(script_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"✗ {script_name} 실행 실패:")
        print(result.stderr)
        sys.exit(1)
    print(f"✓ {script_name} 완료")


def main():
    print("=" * 60)
    print("B0 데이터베이스 리셋")
    print("=" * 60)
    print()

    # 1. 모든 테이블 삭제
    print("[1/3] 테이블 삭제 중...")
    asyncio.run(drop_all_tables())
    print()

    # 2. Alembic 마이그레이션 실행
    print("[2/3] 마이그레이션 실행 중...")
    run_alembic_upgrade()
    print()

    # 3. 시드 스크립트 실행
    print("[3/3] 시드 데이터 생성 중...")
    for script_name in SEED_SCRIPTS:
        run_seed_script(script_name)
    print()

    print("=" * 60)
    print("데이터베이스 리셋 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
