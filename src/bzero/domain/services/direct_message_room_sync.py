"""1:1 대화방 동기 서비스.

Celery Worker에서 사용하는 동기 버전 도메인 서비스입니다.
"""

from bzero.domain.repositories.direct_message_room_sync import DirectMessageRoomSyncRepository
from bzero.domain.value_objects import Id


class DirectMessageRoomSyncService:
    """1:1 대화방 동기 서비스.

    Celery Worker에서 체크아웃 시 DM 종료 등의 작업에 사용됩니다.
    """

    def __init__(self, dm_room_sync_repository: DirectMessageRoomSyncRepository):
        """DirectMessageRoomSyncService를 초기화합니다.

        Args:
            dm_room_sync_repository: 동기 대화방 저장소 인터페이스
        """
        self._dm_room_repository = dm_room_sync_repository

    def end_dm_rooms_by_room_id(self, room_id: Id) -> int:
        """룸 ID로 활성 대화방들을 종료합니다.

        체크아웃 시 해당 룸의 PENDING, ACCEPTED, ACTIVE 상태 대화방을 ENDED로 변경합니다.

        Args:
            room_id: 룸 ID

        Returns:
            종료된 대화방 개수
        """
        return self._dm_room_repository.end_active_dm_rooms_by_room_id(room_id)
