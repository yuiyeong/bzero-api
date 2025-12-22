from bzero.domain.services.room_stay import RoomStayService
from bzero.domain.value_objects import Id


class VerifyRoomAccessUseCase:
    """룸 접근 권한 검증 유스케이스.

    사용자가 특정 룸에 현재 체류(CHECKED_IN) 중인지 확인합니다.
    권한이 없는 경우 ForbiddenRoomForUserError를 발생시킵니다.
    """

    def __init__(self, room_stay_service: RoomStayService):
        """VerifyRoomAccessUseCase를 초기화합니다.

        Args:
            room_stay_service: 체류 도메인 서비스
        """
        self._room_stay_service = room_stay_service

    async def execute(self, user_id: str, room_id: str) -> None:
        """사용자의 룸 접근 권한을 검증합니다.

        Args:
            user_id: 사용자 ID (hex)
            room_id: 룸 ID (hex)

        Raises:
            ForbiddenRoomForUserError: 접근 권한이 없는 경우
        """
        await self._room_stay_service.get_stays_by_user_id_and_room_id(
            user_id=Id.from_hex(user_id),
            room_id=Id.from_hex(room_id),
        )
