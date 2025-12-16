from bzero.application.results import RoomStayResult
from bzero.domain.services import UserService
from bzero.domain.services.room_stay import RoomStayService
from bzero.domain.value_objects import AuthProvider


class GetCurrentStayUseCase:
    """현재 체류 조회 유스케이스.

    사용자의 현재 활성(CHECKED_IN) 체류 정보를 조회합니다.
    """

    def __init__(self, user_service: UserService, room_stay_service: RoomStayService):
        """GetCurrentStayUseCase를 초기화합니다.

        Args:
            user_service: 사용자 도메인 서비스
            room_stay_service: 체류 도메인 서비스
        """
        self._user_service = user_service
        self._room_stay_service = room_stay_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
    ) -> RoomStayResult | None:
        """현재 체류 정보를 조회합니다.

        인증 제공자 정보로 사용자를 조회한 후,
        해당 사용자의 활성 체류를 반환합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID

        Returns:
            현재 체류 결과 또는 None (체류 중이 아닌 경우)
        """
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )
        room_stay = await self._room_stay_service.get_checked_in_by_user_id(user.user_id)
        return RoomStayResult.create_from(room_stay) if room_stay else None
