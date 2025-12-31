from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results import RoomStayResult
from bzero.domain.errors import (
    ForbiddenRoomForUserError,
    InsufficientBalanceError,
    InvalidStayStatusError,
    NoActiveStayError,
)
from bzero.domain.services import UserService
from bzero.domain.services.room_stay import RoomStayService, StayExtensionService
from bzero.domain.value_objects import AuthProvider


class ExtendStayUseCase:
    """체류 연장 유스케이스.

    사용자의 현재 활성(CHECKED_IN) 체류를 연장합니다.
    포인트가 차감됩니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        room_stay_service: RoomStayService,
        stay_extension_service: StayExtensionService,
    ):
        self._session = session
        self._user_service = user_service
        self._room_stay_service = room_stay_service
        self._stay_extension_service = stay_extension_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
    ) -> RoomStayResult:
        """체류 연장을 실행합니다.

        Args:
            provider: 인증 제공자
            provider_user_id: 인증 제공자의 사용자 ID

        Returns:
            연장된 체류 정보

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
            NoActiveStayError: 활성 체류가 없는 경우
            InsufficientBalanceError: 포인트가 부족한 경우
            InvalidStayStatusError: 상태가 올바르지 않은 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. 현재 체류 조회
        current_stay = await self._room_stay_service.get_checked_in_by_user_id(user.user_id)
        if not current_stay:
            raise NoActiveStayError

        # 3. 연장 실행 (서비스 내부에서 락, 포인트 차감)
        try:
            updated_stay = await self._stay_extension_service.extend_stay(
                room_stay_id=current_stay.room_stay_id,
                user_id=user.user_id,
            )

            # 4. 트랜잭션 커밋
            await self._session.commit()

            return RoomStayResult.create_from(updated_stay)

        except (
            InsufficientBalanceError,
            NoActiveStayError,
            InvalidStayStatusError,
            ForbiddenRoomForUserError,
        ):
            await self._session.rollback()
            raise
        except Exception:
            await self._session.rollback()
            raise
