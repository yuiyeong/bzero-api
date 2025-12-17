"""Redis 클라이언트 설정.

Rate Limiting 및 캐싱을 위한 Redis 연결을 관리합니다.
"""

from redis.asyncio import Redis

from bzero.core.settings import get_settings


def get_redis_client() -> Redis:
    """Redis 클라이언트를 생성합니다.

    Returns:
        비동기 Redis 클라이언트 인스턴스
    """
    settings = get_settings()
    return Redis.from_url(
        settings.redis.url,
        encoding="utf-8",
        decode_responses=True,
    )
