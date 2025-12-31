from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results import RoomStayResult
from bzero.domain.errors import ForbiddenRoomForUserError, NoActiveStayError
from bzero.domain.services import UserService
from bzero.domain.services.room_stay import CheckoutService, RoomStayService
from bzero.domain.value_objects import AuthProvider


class CheckoutUseCase:
    """체크아웃 유스케이스.

    사용자의 현재 활성(CHECKED_IN) 체류를 체크아웃합니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        room_stay_service: RoomStayService,
        checkout_service: CheckoutService,
    ):
        self._session = session
        self._user_service = user_service
        self._room_stay_service = room_stay_service
        self._checkout_service = checkout_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
    ) -> RoomStayResult:
        """체크아웃을 실행합니다.

        Args:
            provider: 인증 제공자
            provider_user_id: 인증 제공자의 사용자 ID

        Returns:
            체크아웃된 체류 정보

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
            NoActiveStayError: 활성 체류가 없는 경우
            ForbiddenRoomForUserError: 권한이 없는 경우
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

        # 3. 체크아웃 실행 (서비스 내부에서 락 획득)
        try:
            updated_stay = await self._checkout_service.checkout(
                room_stay_id=current_stay.room_stay_id,
                user_id=user.user_id,
            )

            # 4. 트랜잭션 커밋
            await self._session.commit()

            return RoomStayResult.create_from(updated_stay)

        except (NoActiveStayError, ForbiddenRoomForUserError):
            await self._session.rollback()
            raise
        except Exception:
            await self._session.rollback()
            raise
