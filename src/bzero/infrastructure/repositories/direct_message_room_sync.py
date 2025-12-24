"""DirectMessageRoom 동기 리포지토리 구현체.

Celery Worker에서 사용하는 SqlAlchemy 동기 버전입니다.
"""

from sqlalchemy.orm import Session

from bzero.domain.entities.direct_message_room import DirectMessageRoom
from bzero.domain.repositories.direct_message_room_sync import DirectMessageRoomSyncRepository
from bzero.domain.value_objects import DMStatus, Id
from bzero.infrastructure.repositories.direct_message_room_core import (
    DirectMessageRoomRepositoryCore,
)


class SqlAlchemyDirectMessageRoomSyncRepository(DirectMessageRoomSyncRepository):
    """SqlAlchemy 기반 DirectMessageRoom 동기 리포지토리.

    Celery Worker에서 사용하는 동기 버전입니다.
    Core 메서드를 직접 호출합니다.
    """

    def __init__(self, session: Session):
        self._session = session

    def find_by_id(self, dm_room_id: Id) -> DirectMessageRoom | None:
        """ID로 대화방을 조회합니다."""
        return DirectMessageRoomRepositoryCore.find_by_id(self._session, dm_room_id)

    def find_by_user_and_statuses(
        self,
        user_id: Id,
        statuses: list[DMStatus],
        limit: int = 50,
        offset: int = 0,
    ) -> list[DirectMessageRoom]:
        """사용자와 상태로 대화방 목록을 조회합니다."""
        return DirectMessageRoomRepositoryCore.find_by_user_and_statuses(
            self._session, user_id, statuses, limit, offset
        )

    def update(self, dm_room: DirectMessageRoom) -> DirectMessageRoom:
        """대화방 정보를 업데이트합니다."""
        return DirectMessageRoomRepositoryCore.update(self._session, dm_room)

    def soft_delete_by_room_id(self, room_id: Id) -> int:
        """룸 ID로 대화방들을 soft delete 처리합니다."""
        return DirectMessageRoomRepositoryCore.soft_delete_by_room_id(self._session, room_id)

    def end_active_dm_rooms_by_room_id(self, room_id: Id) -> int:
        """룸 ID로 활성 대화방들을 종료 처리합니다."""
        return DirectMessageRoomRepositoryCore.end_active_dm_rooms_by_room_id(
            self._session, room_id
        )
