"""Redis 기반 Rate Limiter 어댑터.

Redis SET NX를 사용하여 속도 제한 기능을 구현합니다.
"""

from redis.asyncio import Redis

from bzero.domain.ports.rate_limiter import RateLimiter
from bzero.domain.value_objects import Id


class RedisRateLimiter(RateLimiter):
    """Redis 기반 Rate Limiter 구현체.

    Redis SET NX (Set if Not eXists) 명령을 사용하여
    동시성 제어를 보장하는 속도 제한 기능을 제공합니다.

    키 형식: "rate_limit:chat:{user_id}:{room_id}"
    TTL: window_seconds (기본 2초)
    """

    def __init__(self, redis_client: Redis):
        self._redis = redis_client

    async def check_rate_limit(
        self,
        user_id: Id,
        room_id: Id,
        window_seconds: int = 2,
    ) -> bool:
        """속도 제한을 확인합니다.

        Redis SET NX를 사용하여 key가 없을 때만 설정합니다.
        - 성공 (True): 제한 시간 내 첫 요청, 전송 허용
        - 실패 (False): 제한 시간 내 중복 요청, 전송 거부

        Args:
            user_id: 사용자 ID
            room_id: 룸 ID
            window_seconds: 제한 시간 (초) - 기본 2초

        Returns:
            True: 전송 허용
            False: 전송 거부 (429 Too Many Requests)
        """
        key = f"rate_limit:chat:{user_id.to_hex()}:{room_id.to_hex()}"

        # SET NX EX: key가 없으면 설정하고 TTL 지정, 있으면 None 반환
        result = await self._redis.set(
            name=key,
            value="1",
            ex=window_seconds,  # TTL (초)
            nx=True,  # Set if Not eXists
        )

        # result가 True면 설정 성공 (제한 미달), False면 이미 존재 (제한 초과)
        return result is not None
