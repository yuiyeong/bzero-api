"""Rate Limiter 포트 인터페이스.

도메인 계층에서 정의하는 속도 제한 시스템의 추상 인터페이스입니다.
실제 구현은 Infrastructure 계층의 RedisRateLimiter에서 제공합니다.
"""

from abc import ABC, abstractmethod

from bzero.domain.value_objects import Id


class RateLimiter(ABC):
    """Rate Limiter 포트 인터페이스.

    속도 제한 기능을 제공하는 추상 클래스입니다.
    주로 채팅 메시지 전송 제한(2초에 1회)에 사용됩니다.
    """

    @abstractmethod
    async def check_rate_limit(
        self,
        user_id: Id,
        room_id: Id,
        window_seconds: int = 2,
    ) -> bool:
        """속도 제한을 확인합니다.

        Redis SET NX를 사용하여 동시성 제어를 보장합니다.

        Args:
            user_id: 사용자 ID
            room_id: 룸 ID
            window_seconds: 제한 시간 (초) - 기본 2초

        Returns:
            True: 전송 허용 (제한 미달)
            False: 전송 거부 (제한 초과)
        """
