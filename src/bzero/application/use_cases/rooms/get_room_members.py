from bzero.application.results import PaginatedResult, UserResult
from bzero.domain.services import UserService
from bzero.domain.services.room_stay import RoomStayService
from bzero.domain.value_objects import AuthProvider, Id


class GetRoomMembersUseCase:
    """같은 방 멤버 조회 유스케이스.

    특정 방에 체류 중인 멤버 목록을 조회합니다.
    요청한 사용자가 해당 방에 체류 중인 경우에만 조회가 가능합니다.
    """

    def __init__(self, user_service: UserService, room_stay_service: RoomStayService):
        """GetRoomMembersUseCase를 초기화합니다.

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
        room_id: str,
    ) -> PaginatedResult[UserResult]:
        """같은 방에 체류 중인 멤버 목록을 조회합니다.

        인증 제공자 정보로 사용자를 조회한 후,
        해당 사용자가 체류 중인 방의 멤버 목록을 반환합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID
            room_id: 방 ID (UUID v7 hex)

        Returns:
            같은 방 멤버 목록 (UserResult)

        Raises:
            ForbiddenRoomForUserError: 사용자가 해당 방에 체류 중이 아닌 경우
        """
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        room_stays = await self._room_stay_service.get_stays_by_user_id_and_room_id(
            user.user_id,
            Id.from_hex(room_id),
        )

        member_ids = [room_stay.user_id for room_stay in room_stays]
        members = await self._user_service.get_users_by_user_ids(member_ids)

        user_results = [UserResult.create_from(member) for member in members]
        return PaginatedResult(
            items=user_results,
            total=len(members),
            offset=0,
            limit=len(members),
        )
